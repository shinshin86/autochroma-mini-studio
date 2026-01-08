"""FastAPI application for AutoChroma Mini Studio."""
from fastapi import FastAPI, HTTPException, UploadFile, File, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response, JSONResponse

from .ffmpeg_tools import (
    check_ffmpeg,
    get_video_metadata,
    get_image_metadata,
    estimate_background_color,
    generate_preview,
)
from .jobs import JobManager, get_job_manager
from .models import (
    AssetType,
    ProbeResponse,
    AssetResponse,
    EstimateKeyResponse,
    RGBColor,
    PreviewRequest,
    RenderRequest,
    RenderResponse,
    JobResponse,
    CancelResponse,
)
from .settings import CORS_ORIGINS, MAX_UPLOAD_SIZE, UPLOAD_CHUNK_SIZE, setup_logging, get_logger

# Initialize logging
setup_logging()
logger = get_logger(__name__)

from .storage import (
    generate_id,
    safe_filename,
    get_extension,
    get_asset_path,
    find_asset_path,
    get_output_path,
    get_preview_path,
    is_video_extension,
    is_image_extension,
    get_valid_extensions,
    InvalidIdError,
)

app = FastAPI(
    title="AutoChroma Mini Studio API",
    description="API for video chromakey transparency processing",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(InvalidIdError)
async def invalid_id_exception_handler(request: Request, exc: InvalidIdError):
    """Handle invalid ID format errors."""
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.get("/api/probe", response_model=ProbeResponse)
async def probe_ffmpeg():
    """Check if ffmpeg and ffprobe are available."""
    ok, ffmpeg_version, ffprobe_version = check_ffmpeg()

    if not ok:
        return ProbeResponse(
            ok=False,
            message="ffmpeg or ffprobe not found. Install ffmpeg and ensure it is in PATH."
        )

    return ProbeResponse(
        ok=True,
        ffmpeg=ffmpeg_version,
        ffprobe=ffprobe_version
    )


@app.post("/api/assets", response_model=AssetResponse)
async def upload_asset(file: UploadFile = File(...)):
    """Upload a video or image file."""
    logger.info(f"Upload request received: {file.filename}")
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    # Validate file extension
    extension = get_extension(file.filename)
    valid_extensions = get_valid_extensions()
    if extension not in valid_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Supported formats: {', '.join(sorted(valid_extensions))}"
        )

    # Determine asset type
    is_video = is_video_extension(extension)
    asset_type = AssetType.VIDEO if is_video else AssetType.IMAGE

    asset_id = generate_id()
    asset_path = get_asset_path(asset_id, extension)

    # Save uploaded file with chunked reading and size limit
    try:
        total_size = 0
        with open(asset_path, "wb") as f:
            while chunk := await file.read(UPLOAD_CHUNK_SIZE):
                total_size += len(chunk)
                if total_size > MAX_UPLOAD_SIZE:
                    f.close()
                    asset_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Maximum size is {MAX_UPLOAD_SIZE // (1024 * 1024)}MB"
                    )
                f.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        asset_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    # Get metadata based on asset type
    try:
        if is_video:
            metadata = get_video_metadata(asset_path)
            logger.info(f"Asset uploaded: id={asset_id}, type=video, size={total_size}, dimensions={metadata.width}x{metadata.height}")
            return AssetResponse(
                asset_id=asset_id,
                filename=safe_filename(file.filename),
                asset_type=asset_type,
                width=metadata.width,
                height=metadata.height,
                duration=round(metadata.duration, 2),
                fps=metadata.fps,
                has_audio=metadata.has_audio
            )
        else:
            metadata = get_image_metadata(asset_path)
            logger.info(f"Asset uploaded: id={asset_id}, type=image, size={total_size}, dimensions={metadata.width}x{metadata.height}")
            return AssetResponse(
                asset_id=asset_id,
                filename=safe_filename(file.filename),
                asset_type=asset_type,
                width=metadata.width,
                height=metadata.height,
                duration=None,
                fps=None,
                has_audio=None
            )
    except Exception as e:
        # Clean up on failure
        logger.error(f"Failed to read metadata for asset {asset_id}: {e}")
        asset_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=400,
            detail=f"Failed to read file metadata. Is this a valid {'video' if is_video else 'image'} file? Error: {e}"
        )


@app.post("/api/assets/{asset_id}/estimate-key", response_model=EstimateKeyResponse)
async def estimate_key(asset_id: str):
    """Estimate background key color for chromakey."""
    asset_path = find_asset_path(asset_id)
    if not asset_path:
        raise HTTPException(status_code=404, detail="Asset not found")

    try:
        # Determine if video or image
        extension = get_extension(asset_path.name)
        is_video = is_video_extension(extension)

        if is_video:
            metadata = get_video_metadata(asset_path)
            hex_color, rgb, samples = estimate_background_color(asset_path, metadata.duration)
        else:
            # For images, duration is None
            hex_color, rgb, samples = estimate_background_color(asset_path, None)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to estimate background color: {e}"
        )

    return EstimateKeyResponse(
        hex=hex_color,
        rgb=RGBColor(r=rgb[0], g=rgb[1], b=rgb[2]),
        samples=samples
    )


@app.post("/api/assets/{asset_id}/preview")
async def create_preview(asset_id: str, request: PreviewRequest):
    """Generate preview image with chromakey applied."""
    asset_path = find_asset_path(asset_id)
    if not asset_path:
        raise HTTPException(status_code=404, detail="Asset not found")

    # Determine if video or image
    extension = get_extension(asset_path.name)
    is_video = is_video_extension(extension)

    # Validate and get time for videos, None for images
    time = None
    if is_video:
        try:
            metadata = get_video_metadata(asset_path)
            if request.time is not None:
                time = min(request.time, metadata.duration - 0.1)
                time = max(0, time)
            else:
                time = 0.5
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to read video: {e}")

    preview_id = generate_id()
    preview_path = get_preview_path(preview_id)

    try:
        generate_preview(
            input_path=asset_path,
            output_path=preview_path,
            hex_color=request.hex.upper(),
            similarity=request.similarity,
            blend=request.blend,
            time=time,
            max_width=request.max_width
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate preview: {e}"
        )

    # Read and return PNG
    with open(preview_path, "rb") as f:
        png_data = f.read()

    return Response(
        content=png_data,
        media_type="image/png",
        headers={"X-Preview-Id": preview_id}
    )


@app.post("/api/assets/{asset_id}/render", response_model=RenderResponse)
async def start_render(
    asset_id: str,
    request: RenderRequest,
    job_manager: JobManager = Depends(get_job_manager)
):
    """Start render job for transparent output (WebM for video, PNG for image)."""
    asset_path = find_asset_path(asset_id)
    if not asset_path:
        raise HTTPException(status_code=404, detail="Asset not found")

    # Determine asset type
    extension = get_extension(asset_path.name)
    is_video = is_video_extension(extension)
    asset_type = AssetType.VIDEO if is_video else AssetType.IMAGE

    job_id = job_manager.create_job(
        asset_id=asset_id,
        input_path=asset_path,
        asset_type=asset_type,
        hex_color=request.hex.upper(),
        similarity=request.similarity,
        blend=request.blend,
        crf=request.crf if is_video else None,
        include_audio=request.include_audio if is_video else False
    )

    return RenderResponse(job_id=job_id)


@app.get("/api/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(
    job_id: str,
    job_manager: JobManager = Depends(get_job_manager)
):
    """Get job status and progress."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Determine output extension based on asset type
    is_video = job.asset_type == AssetType.VIDEO
    output_ext = "webm" if is_video else "png"
    output_path = get_output_path(job_id, output_ext)
    output_size = output_path.stat().st_size if output_path.exists() else None

    return JobResponse(
        job_id=job.job_id,
        status=job.status,
        progress=round(job.progress, 3),
        message=job.message,
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
        output_filename=f"out.{output_ext}" if output_path.exists() else None,
        output_size_bytes=output_size,
        last_log_lines=job.log_lines[-10:]
    )


@app.post("/api/jobs/{job_id}/cancel", response_model=CancelResponse)
async def cancel_job(
    job_id: str,
    job_manager: JobManager = Depends(get_job_manager)
):
    """Cancel a running job."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    success = job_manager.cancel_job(job_id)
    return CancelResponse(ok=success)


@app.get("/api/jobs/{job_id}/download")
async def download_output(
    job_id: str,
    job_manager: JobManager = Depends(get_job_manager)
):
    """Download the rendered output file."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != "done":
        raise HTTPException(
            status_code=400,
            detail=f"Job is not complete. Current status: {job.status}"
        )

    # Determine output based on asset type
    is_video = job.asset_type == AssetType.VIDEO
    output_ext = "webm" if is_video else "png"
    media_type = "video/webm" if is_video else "image/png"
    filename = f"output.{output_ext}"

    output_path = get_output_path(job_id, output_ext)
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="Output file not found")

    return FileResponse(
        path=output_path,
        media_type=media_type,
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

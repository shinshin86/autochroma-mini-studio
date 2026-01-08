"""FFmpeg utilities for video and image processing."""
import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from typing import Optional


class InvalidParameterError(ValueError):
    """Raised when a parameter fails validation."""
    pass


def validate_hex_color(hex_color: str) -> str:
    """Validate and normalize hex color string.

    Args:
        hex_color: Hex color string (e.g., "00FF00" or "#00FF00")

    Returns:
        Normalized uppercase hex color without '#' prefix

    Raises:
        InvalidParameterError: If the color format is invalid
    """
    color = hex_color.lstrip("#").upper()
    if not re.match(r"^[0-9A-F]{6}$", color):
        raise InvalidParameterError(
            f"Invalid hex color format: {hex_color}. Expected 6 hex characters (e.g., '00FF00')"
        )
    return color


def validate_chromakey_params(similarity: float, blend: float) -> tuple[float, float]:
    """Validate chromakey similarity and blend parameters.

    Args:
        similarity: Similarity threshold (0.0-1.0)
        blend: Blend amount (0.0-1.0)

    Returns:
        Tuple of validated (similarity, blend)

    Raises:
        InvalidParameterError: If parameters are out of range
    """
    if not isinstance(similarity, (int, float)) or not (0.0 <= similarity <= 1.0):
        raise InvalidParameterError(
            f"Invalid similarity value: {similarity}. Must be between 0.0 and 1.0"
        )
    if not isinstance(blend, (int, float)) or not (0.0 <= blend <= 1.0):
        raise InvalidParameterError(
            f"Invalid blend value: {blend}. Must be between 0.0 and 1.0"
        )
    return float(similarity), float(blend)


@dataclass
class VideoMetadata:
    """Video metadata from ffprobe."""
    duration: float
    width: int
    height: int
    fps: float
    has_audio: bool


@dataclass
class ImageMetadata:
    """Image metadata from ffprobe."""
    width: int
    height: int


class FFmpegCheckError(Exception):
    """Raised when ffmpeg/ffprobe check fails."""
    pass


def check_ffmpeg() -> tuple[bool, Optional[str], Optional[str]]:
    """Check if ffmpeg and ffprobe are available.

    Returns:
        Tuple of (ok, ffmpeg_version, ffprobe_version)

    Note:
        Returns (False, None, None) if tools are not found or not executable.
        Specific errors are logged but not raised to allow graceful degradation.
    """
    ffmpeg_path = shutil.which("ffmpeg")
    ffprobe_path = shutil.which("ffprobe")

    if not ffmpeg_path or not ffprobe_path:
        return False, None, None

    try:
        ffmpeg_result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        ffprobe_result = subprocess.run(
            ["ffprobe", "-version"],
            capture_output=True,
            text=True,
            timeout=10
        )

        ffmpeg_version = ffmpeg_result.stdout.split("\n")[0] if ffmpeg_result.returncode == 0 else None
        ffprobe_version = ffprobe_result.stdout.split("\n")[0] if ffprobe_result.returncode == 0 else None

        return True, ffmpeg_version, ffprobe_version
    except subprocess.TimeoutExpired:
        # ffmpeg check timed out - may indicate system issues
        return False, None, None
    except subprocess.SubprocessError as e:
        # Subprocess execution failed
        return False, None, None
    except OSError as e:
        # File not found or permission denied
        return False, None, None


def get_video_metadata(video_path: Path) -> VideoMetadata:
    """Get video metadata using ffprobe."""
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(video_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr}")

    data = json.loads(result.stdout)

    # Find video stream
    video_stream = None
    has_audio = False

    for stream in data.get("streams", []):
        if stream.get("codec_type") == "video" and video_stream is None:
            video_stream = stream
        elif stream.get("codec_type") == "audio":
            has_audio = True

    if not video_stream:
        raise RuntimeError("No video stream found in file")

    # Parse duration
    duration = float(data.get("format", {}).get("duration", 0))
    if duration == 0:
        duration = float(video_stream.get("duration", 0))

    # Parse dimensions
    width = int(video_stream.get("width", 0))
    height = int(video_stream.get("height", 0))

    # Parse FPS
    fps_str = video_stream.get("r_frame_rate", "30/1")
    if "/" in fps_str:
        num, den = fps_str.split("/")
        fps = float(num) / float(den) if float(den) != 0 else 30.0
    else:
        fps = float(fps_str)

    return VideoMetadata(
        duration=duration,
        width=width,
        height=height,
        fps=round(fps, 2),
        has_audio=has_audio
    )


def get_image_metadata(image_path: Path) -> ImageMetadata:
    """Get image metadata using ffprobe."""
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        str(image_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr}")

    data = json.loads(result.stdout)

    # Find video/image stream
    image_stream = None
    for stream in data.get("streams", []):
        if stream.get("codec_type") == "video":
            image_stream = stream
            break

    if not image_stream:
        raise RuntimeError("No image stream found in file")

    width = int(image_stream.get("width", 0))
    height = int(image_stream.get("height", 0))

    return ImageMetadata(width=width, height=height)


def sample_color_at_region(
    file_path: Path,
    crop_filter: str,
    time: Optional[float] = None
) -> Optional[tuple[int, int, int]]:
    """Sample average color at a specific region and optional time (for videos)."""
    cmd = ["ffmpeg"]

    # Add time seek only for videos (when time is provided)
    if time is not None:
        cmd.extend(["-ss", str(time)])

    cmd.extend([
        "-i", str(file_path),
        "-vf", f"{crop_filter},scale=1:1",
        "-frames:v", "1",
        "-f", "rawvideo",
        "-pix_fmt", "rgb24",
        "-"
    ])

    result = subprocess.run(
        cmd,
        capture_output=True,
        timeout=30
    )

    if result.returncode != 0 or len(result.stdout) < 3:
        return None

    r, g, b = result.stdout[0], result.stdout[1], result.stdout[2]
    return (r, g, b)


def estimate_background_color(
    file_path: Path,
    duration: Optional[float] = None
) -> tuple[str, tuple[int, int, int], int]:
    """
    Estimate background color by sampling corners.
    For videos: samples at multiple timestamps.
    For images: samples corners once (no time parameter).
    Returns (hex, rgb_tuple, sample_count).
    """
    # Corner crop filters
    corners = [
        "crop=20:20:0:0",           # Top-left
        "crop=20:20:iw-20:0",       # Top-right
        "crop=20:20:0:ih-20",       # Bottom-left
        "crop=20:20:iw-20:ih-20",   # Bottom-right
    ]

    r_values = []
    g_values = []
    b_values = []

    # Determine if this is a video (has duration) or image
    is_video = duration is not None and duration > 0

    if is_video:
        # For videos: sample at multiple timestamps
        timestamps = [0.0, 0.5, 1.0]
        timestamps = [min(t, max(0, duration - 0.1)) for t in timestamps]

        for t in timestamps:
            for crop in corners:
                color = sample_color_at_region(file_path, crop, time=t)
                if color:
                    r_values.append(color[0])
                    g_values.append(color[1])
                    b_values.append(color[2])
    else:
        # For images: sample corners once (no time parameter)
        for crop in corners:
            color = sample_color_at_region(file_path, crop, time=None)
            if color:
                r_values.append(color[0])
                g_values.append(color[1])
                b_values.append(color[2])

    if not r_values:
        raise RuntimeError("Failed to sample any colors from file")

    # Use median for robustness
    r = int(median(r_values))
    g = int(median(g_values))
    b = int(median(b_values))

    hex_color = f"{r:02X}{g:02X}{b:02X}"

    return hex_color, (r, g, b), len(r_values)


def generate_preview(
    input_path: Path,
    output_path: Path,
    hex_color: str,
    similarity: float,
    blend: float,
    time: Optional[float] = None,
    max_width: int = 640
) -> None:
    """Generate preview PNG with chromakey applied.

    For videos, time specifies which frame to use.
    For images, time is ignored.
    """
    # Validate parameters to prevent command injection
    validated_color = validate_hex_color(hex_color)
    validated_similarity, validated_blend = validate_chromakey_params(similarity, blend)

    vf = f"chromakey=0x{validated_color}:{validated_similarity}:{validated_blend},format=rgba,scale={max_width}:-1"

    cmd = ["ffmpeg", "-y"]

    # Add time seek only for videos (when time is provided)
    if time is not None:
        cmd.extend(["-ss", str(time)])

    cmd.extend([
        "-i", str(input_path),
        "-vf", vf,
        "-frames:v", "1",
        "-f", "image2",
        str(output_path)
    ])

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

    if result.returncode != 0:
        raise RuntimeError(f"Preview generation failed: {result.stderr}")


def get_duration_ms(video_path: Path) -> int:
    """Get video duration in milliseconds."""
    metadata = get_video_metadata(video_path)
    return int(metadata.duration * 1000)


def build_render_command(
    input_path: Path,
    output_path: Path,
    hex_color: str,
    similarity: float,
    blend: float,
    crf: int,
    include_audio: bool,
    has_audio: bool
) -> list[str]:
    """Build ffmpeg command for rendering transparent WebM."""
    # Validate parameters to prevent command injection
    validated_color = validate_hex_color(hex_color)
    validated_similarity, validated_blend = validate_chromakey_params(similarity, blend)

    vf = f"chromakey=0x{validated_color}:{validated_similarity}:{validated_blend},format=yuva420p"

    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(input_path),
        "-vf", vf,
        "-c:v", "libvpx-vp9",
        "-b:v", "0",
        "-crf", str(crf),
        "-auto-alt-ref", "0",
        "-pix_fmt", "yuva420p",
    ]

    if include_audio and has_audio:
        cmd.extend(["-c:a", "libopus", "-b:a", "128k"])
    else:
        cmd.append("-an")

    cmd.extend([
        "-progress", "pipe:1",
        "-nostats",
        str(output_path)
    ])

    return cmd


def build_image_render_command(
    input_path: Path,
    output_path: Path,
    hex_color: str,
    similarity: float,
    blend: float
) -> list[str]:
    """Build ffmpeg command for rendering transparent PNG from image."""
    # Validate parameters to prevent command injection
    validated_color = validate_hex_color(hex_color)
    validated_similarity, validated_blend = validate_chromakey_params(similarity, blend)

    vf = f"chromakey=0x{validated_color}:{validated_similarity}:{validated_blend},format=rgba"

    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(input_path),
        "-vf", vf,
        "-f", "image2",
        str(output_path)
    ]

    return cmd


def parse_progress(line: str) -> Optional[int]:
    """Parse out_time_ms from ffmpeg progress output."""
    if line.startswith("out_time_ms="):
        try:
            return int(line.split("=")[1])
        except (ValueError, IndexError):
            pass
    return None

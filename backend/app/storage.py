"""Storage utilities for file management."""
import re
import uuid
from pathlib import Path
from typing import Optional

from .settings import ASSETS_DIR, OUTPUTS_DIR, PREVIEWS_DIR, LOGS_DIR


class InvalidIdError(ValueError):
    """Raised when an ID fails validation."""
    pass


def generate_id() -> str:
    """Generate a unique ID."""
    return str(uuid.uuid4())


def validate_id(id_value: str) -> str:
    """Validate that an ID is a valid UUID4 format.

    Prevents path traversal attacks by ensuring IDs are valid UUIDs.

    Args:
        id_value: The ID to validate

    Returns:
        The validated ID (unchanged)

    Raises:
        InvalidIdError: If the ID is not a valid UUID
    """
    try:
        parsed = uuid.UUID(id_value, version=4)
        if str(parsed) != id_value.lower():
            raise InvalidIdError(f"Invalid ID format: {id_value}")
        return id_value
    except ValueError:
        raise InvalidIdError(f"Invalid ID format: {id_value}")


def safe_filename(filename: str) -> str:
    """Sanitize filename to be safe for filesystem."""
    # Keep only alphanumeric, dash, underscore, dot
    name = re.sub(r"[^\w\-.]", "_", filename)
    # Prevent hidden files
    name = name.lstrip(".")
    # Limit length
    if len(name) > 200:
        name = name[:200]
    return name or "file"


def get_extension(filename: str) -> str:
    """Get file extension from filename."""
    return Path(filename).suffix.lower()


# Valid file extensions
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".gif"}


def is_video_extension(extension: str) -> bool:
    """Check if extension is a video format."""
    return extension.lower() in VIDEO_EXTENSIONS


def is_image_extension(extension: str) -> bool:
    """Check if extension is an image format."""
    return extension.lower() in IMAGE_EXTENSIONS


def get_valid_extensions() -> set[str]:
    """Get all valid file extensions."""
    return VIDEO_EXTENSIONS | IMAGE_EXTENSIONS


def get_asset_dir(asset_id: str) -> Path:
    """Get directory for an asset."""
    validate_id(asset_id)
    path = ASSETS_DIR / asset_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_asset_path(asset_id: str, extension: str) -> Path:
    """Get path for asset input file."""
    return get_asset_dir(asset_id) / f"input{extension}"


def find_asset_path(asset_id: str) -> Optional[Path]:
    """Find the input file for an asset."""
    validate_id(asset_id)
    asset_dir = ASSETS_DIR / asset_id
    if not asset_dir.exists():
        return None
    for f in asset_dir.iterdir():
        if f.name.startswith("input"):
            return f
    return None


def get_output_dir(job_id: str) -> Path:
    """Get directory for job output."""
    validate_id(job_id)
    path = OUTPUTS_DIR / job_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_output_path(job_id: str, extension: str = "webm") -> Path:
    """Get path for output file. Extension should be 'webm' for video, 'png' for image."""
    return get_output_dir(job_id) / f"out.{extension}"


def get_preview_dir(preview_id: str) -> Path:
    """Get directory for preview."""
    validate_id(preview_id)
    path = PREVIEWS_DIR / preview_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_preview_path(preview_id: str) -> Path:
    """Get path for preview image."""
    return get_preview_dir(preview_id) / "preview.png"


def get_log_path(job_id: str) -> Path:
    """Get path for job log file."""
    validate_id(job_id)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    return LOGS_DIR / f"{job_id}.log"

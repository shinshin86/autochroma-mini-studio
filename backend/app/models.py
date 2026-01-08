"""Pydantic models for API requests and responses."""
from datetime import datetime
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field


class AssetType(str, Enum):
    """Asset type enum."""
    VIDEO = "video"
    IMAGE = "image"


class RGBColor(BaseModel):
    """RGB color representation."""
    r: int = Field(ge=0, le=255)
    g: int = Field(ge=0, le=255)
    b: int = Field(ge=0, le=255)


class ProbeResponse(BaseModel):
    """Response for ffmpeg probe check."""
    ok: bool
    ffmpeg: Optional[str] = None
    ffprobe: Optional[str] = None
    message: Optional[str] = None


class AssetResponse(BaseModel):
    """Response after uploading an asset."""
    asset_id: str
    filename: str
    asset_type: AssetType
    width: int
    height: int
    # Video-only fields (None for images)
    duration: Optional[float] = None
    fps: Optional[float] = None
    has_audio: Optional[bool] = None


class EstimateKeyResponse(BaseModel):
    """Response for background color estimation."""
    hex: str
    rgb: RGBColor
    samples: int


class PreviewRequest(BaseModel):
    """Request for generating preview image."""
    hex: str = Field(pattern=r"^[0-9A-Fa-f]{6}$")
    similarity: float = Field(ge=0.0, le=1.0, default=0.10)
    blend: float = Field(ge=0.0, le=1.0, default=0.05)
    time: Optional[float] = Field(ge=0.0, default=0.5)  # Ignored for images
    max_width: int = Field(ge=100, le=1920, default=640)


class RenderRequest(BaseModel):
    """Request for starting render job."""
    hex: str = Field(pattern=r"^[0-9A-Fa-f]{6}$")
    similarity: float = Field(ge=0.0, le=1.0, default=0.10)
    blend: float = Field(ge=0.0, le=1.0, default=0.05)
    # Video-only options (ignored for images)
    crf: Optional[int] = Field(ge=10, le=63, default=24)
    include_audio: Optional[bool] = True


class RenderResponse(BaseModel):
    """Response after starting render job."""
    job_id: str


class JobStatus(str, Enum):
    """Job status enum."""
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"
    CANCELED = "canceled"


class JobResponse(BaseModel):
    """Response for job status."""
    job_id: str
    status: JobStatus
    progress: float = 0.0
    message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    output_filename: Optional[str] = None
    output_size_bytes: Optional[int] = None
    last_log_lines: list[str] = []


class CancelResponse(BaseModel):
    """Response for job cancellation."""
    ok: bool


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: Optional[str] = None

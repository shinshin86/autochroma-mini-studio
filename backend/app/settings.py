"""Application settings and configuration."""
import logging
import sys
from pathlib import Path

# Base directories
BACKEND_DIR = Path(__file__).parent.parent
DATA_DIR = BACKEND_DIR / ".data"
ASSETS_DIR = DATA_DIR / "assets"
OUTPUTS_DIR = DATA_DIR / "outputs"
PREVIEWS_DIR = DATA_DIR / "previews"
LOGS_DIR = DATA_DIR / "logs"

# Ensure directories exist
for dir_path in [DATA_DIR, ASSETS_DIR, OUTPUTS_DIR, PREVIEWS_DIR, LOGS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# CORS settings
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# FFmpeg settings
FFMPEG_TIMEOUT = 3600  # 1 hour max for rendering
PREVIEW_MAX_WIDTH = 640

# Upload settings
MAX_UPLOAD_SIZE = 500 * 1024 * 1024  # 500MB max file size
UPLOAD_CHUNK_SIZE = 1024 * 1024  # 1MB chunks for streaming uploads

# Logging configuration
LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def setup_logging() -> None:
    """Configure application logging."""
    logging.basicConfig(
        level=LOG_LEVEL,
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger for the given module name."""
    return logging.getLogger(name)

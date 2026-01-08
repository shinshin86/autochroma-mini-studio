"""Shared test fixtures."""
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.jobs import set_job_manager, JobManager


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def mock_storage_dirs(temp_dir):
    """Mock the storage directories to use temp directory."""
    with patch("app.storage.ASSETS_DIR", temp_dir / "assets"), \
         patch("app.storage.OUTPUTS_DIR", temp_dir / "outputs"), \
         patch("app.storage.PREVIEWS_DIR", temp_dir / "previews"), \
         patch("app.storage.LOGS_DIR", temp_dir / "logs"):
        (temp_dir / "assets").mkdir()
        (temp_dir / "outputs").mkdir()
        (temp_dir / "previews").mkdir()
        (temp_dir / "logs").mkdir()
        yield temp_dir


@pytest.fixture
def job_manager():
    """Create a fresh JobManager for testing."""
    manager = JobManager()
    set_job_manager(manager)
    yield manager
    set_job_manager(None)

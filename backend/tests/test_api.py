"""Tests for API endpoints."""
import io
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.jobs import set_job_manager, JobManager, Job
from app.models import AssetType, JobStatus


@pytest.fixture
def client():
    """Create a test client."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def mock_job_manager():
    """Create a mock JobManager."""
    manager = JobManager()
    set_job_manager(manager)
    yield manager
    set_job_manager(None)


class TestProbeEndpoint:
    """Tests for /api/probe endpoint."""

    def test_probe_ffmpeg_available(self, client):
        """Probe should succeed when ffmpeg is available."""
        with patch("app.main.check_ffmpeg") as mock_check:
            mock_check.return_value = (True, "ffmpeg version 5.0", "ffprobe version 5.0")

            response = client.get("/api/probe")

            assert response.status_code == 200
            data = response.json()
            assert data["ok"] is True
            assert "ffmpeg" in data["ffmpeg"]

    def test_probe_ffmpeg_not_available(self, client):
        """Probe should indicate failure when ffmpeg is not available."""
        with patch("app.main.check_ffmpeg") as mock_check:
            mock_check.return_value = (False, None, None)

            response = client.get("/api/probe")

            assert response.status_code == 200
            data = response.json()
            assert data["ok"] is False
            assert "not found" in data["message"].lower()


class TestUploadEndpoint:
    """Tests for /api/assets upload endpoint."""

    def test_upload_invalid_extension(self, client):
        """Upload should reject invalid file extensions."""
        file_content = b"fake file content"
        files = {"file": ("test.exe", io.BytesIO(file_content), "application/x-msdownload")}

        response = client.post("/api/assets", files=files)

        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]

    def test_upload_no_filename(self, client):
        """Upload should reject files without filename."""
        file_content = b"fake file content"
        files = {"file": ("", io.BytesIO(file_content), "video/mp4")}

        response = client.post("/api/assets", files=files)

        # FastAPI returns 422 for validation errors
        assert response.status_code in (400, 422)

    def test_upload_valid_video(self, client, temp_dir):
        """Upload should accept valid video files."""
        file_content = b"fake video content"

        with patch("app.main.generate_id", return_value="test-asset-id"), \
             patch("app.main.get_asset_path", return_value=temp_dir / "input.mp4"), \
             patch("app.main.get_video_metadata") as mock_metadata:

            mock_metadata.return_value = MagicMock(
                width=1920,
                height=1080,
                duration=10.5,
                fps=30.0,
                has_audio=True
            )

            files = {"file": ("test.mp4", io.BytesIO(file_content), "video/mp4")}
            response = client.post("/api/assets", files=files)

            assert response.status_code == 200
            data = response.json()
            assert data["asset_id"] == "test-asset-id"
            assert data["asset_type"] == "video"
            assert data["width"] == 1920
            assert data["height"] == 1080

    def test_upload_valid_image(self, client, temp_dir):
        """Upload should accept valid image files."""
        file_content = b"fake image content"

        with patch("app.main.generate_id", return_value="test-asset-id"), \
             patch("app.main.get_asset_path", return_value=temp_dir / "input.png"), \
             patch("app.main.get_image_metadata") as mock_metadata:

            mock_metadata.return_value = MagicMock(
                width=1920,
                height=1080
            )

            files = {"file": ("test.png", io.BytesIO(file_content), "image/png")}
            response = client.post("/api/assets", files=files)

            assert response.status_code == 200
            data = response.json()
            assert data["asset_id"] == "test-asset-id"
            assert data["asset_type"] == "image"
            assert data["duration"] is None


class TestEstimateKeyEndpoint:
    """Tests for /api/assets/{asset_id}/estimate-key endpoint."""

    def test_estimate_key_not_found(self, client):
        """Estimate key should return 404 for missing asset."""
        with patch("app.main.find_asset_path", return_value=None):
            response = client.post("/api/assets/nonexistent-id/estimate-key")
            assert response.status_code == 404

    def test_estimate_key_success(self, client, temp_dir):
        """Estimate key should return color estimation."""
        input_path = temp_dir / "input.mp4"
        input_path.touch()

        with patch("app.main.find_asset_path", return_value=input_path), \
             patch("app.main.get_extension", return_value=".mp4"), \
             patch("app.main.is_video_extension", return_value=True), \
             patch("app.main.get_video_metadata") as mock_meta, \
             patch("app.main.estimate_background_color") as mock_estimate:

            mock_meta.return_value = MagicMock(duration=10.0)
            mock_estimate.return_value = ("00FF00", (0, 255, 0), 12)

            response = client.post("/api/assets/test-asset-id/estimate-key")

            assert response.status_code == 200
            data = response.json()
            assert data["hex"] == "00FF00"
            assert data["rgb"]["r"] == 0
            assert data["rgb"]["g"] == 255
            assert data["rgb"]["b"] == 0
            assert data["samples"] == 12


class TestPreviewEndpoint:
    """Tests for /api/assets/{asset_id}/preview endpoint."""

    def test_preview_not_found(self, client):
        """Preview should return 404 for missing asset."""
        with patch("app.main.find_asset_path", return_value=None):
            response = client.post(
                "/api/assets/nonexistent-id/preview",
                json={"hex": "00FF00", "similarity": 0.4, "blend": 0.1, "max_width": 640}
            )
            assert response.status_code == 404

    def test_preview_invalid_hex(self, client, temp_dir):
        """Preview should reject invalid hex color."""
        input_path = temp_dir / "input.mp4"
        input_path.touch()

        with patch("app.main.find_asset_path", return_value=input_path):
            response = client.post(
                "/api/assets/test-asset-id/preview",
                json={"hex": "GGHHII", "similarity": 0.4, "blend": 0.1, "max_width": 640}
            )
            assert response.status_code == 422  # Validation error


class TestRenderEndpoint:
    """Tests for /api/assets/{asset_id}/render endpoint."""

    def test_render_not_found(self, client, mock_job_manager):
        """Render should return 404 for missing asset."""
        with patch("app.main.find_asset_path", return_value=None):
            response = client.post(
                "/api/assets/nonexistent-id/render",
                json={"hex": "00FF00", "similarity": 0.4, "blend": 0.1}
            )
            assert response.status_code == 404

    def test_render_starts_job(self, client, mock_job_manager, temp_dir):
        """Render should start a job and return job ID."""
        input_path = temp_dir / "input.mp4"
        input_path.touch()

        with patch("app.main.find_asset_path", return_value=input_path), \
             patch("app.main.get_extension", return_value=".mp4"), \
             patch("app.main.is_video_extension", return_value=True), \
             patch.object(mock_job_manager, "create_job", return_value="test-job-id"):

            response = client.post(
                "/api/assets/test-asset-id/render",
                json={"hex": "00FF00", "similarity": 0.4, "blend": 0.1}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["job_id"] == "test-job-id"


class TestJobStatusEndpoint:
    """Tests for /api/jobs/{job_id} endpoint."""

    def test_job_status_not_found(self, client, mock_job_manager):
        """Job status should return 404 for missing job."""
        response = client.get("/api/jobs/nonexistent-id")
        assert response.status_code == 404

    def test_job_status_success(self, client, mock_job_manager, temp_dir):
        """Job status should return job information."""
        # Add a job to the manager
        job = Job(
            job_id="test-job-id",
            asset_id="asset-123",
            input_path=temp_dir / "input.mp4",
            asset_type=AssetType.VIDEO,
            hex_color="00FF00",
            similarity=0.4,
            blend=0.1,
            status=JobStatus.RUNNING,
            progress=0.5
        )
        mock_job_manager._jobs["test-job-id"] = job

        with patch("app.main.get_output_path") as mock_output:
            mock_path = MagicMock()
            mock_path.exists.return_value = False
            mock_output.return_value = mock_path

            response = client.get("/api/jobs/test-job-id")

            assert response.status_code == 200
            data = response.json()
            assert data["job_id"] == "test-job-id"
            assert data["status"] == "running"
            assert data["progress"] == 0.5


class TestCancelJobEndpoint:
    """Tests for /api/jobs/{job_id}/cancel endpoint."""

    def test_cancel_job_not_found(self, client, mock_job_manager):
        """Cancel should return 404 for missing job."""
        response = client.post("/api/jobs/nonexistent-id/cancel")
        assert response.status_code == 404

    def test_cancel_job_success(self, client, mock_job_manager, temp_dir):
        """Cancel should cancel a running job."""
        job = Job(
            job_id="test-job-id",
            asset_id="asset-123",
            input_path=temp_dir / "input.mp4",
            asset_type=AssetType.VIDEO,
            hex_color="00FF00",
            similarity=0.4,
            blend=0.1,
            status=JobStatus.RUNNING
        )
        mock_job_manager._jobs["test-job-id"] = job

        response = client.post("/api/jobs/test-job-id/cancel")

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True


class TestDownloadEndpoint:
    """Tests for /api/jobs/{job_id}/download endpoint."""

    def test_download_not_found(self, client, mock_job_manager):
        """Download should return 404 for missing job."""
        response = client.get("/api/jobs/nonexistent-id/download")
        assert response.status_code == 404

    def test_download_not_complete(self, client, mock_job_manager, temp_dir):
        """Download should return 400 for incomplete job."""
        job = Job(
            job_id="test-job-id",
            asset_id="asset-123",
            input_path=temp_dir / "input.mp4",
            asset_type=AssetType.VIDEO,
            hex_color="00FF00",
            similarity=0.4,
            blend=0.1,
            status=JobStatus.RUNNING
        )
        mock_job_manager._jobs["test-job-id"] = job

        response = client.get("/api/jobs/test-job-id/download")

        assert response.status_code == 400
        assert "not complete" in response.json()["detail"]


class TestInvalidIdHandling:
    """Tests for invalid ID handling."""

    def test_invalid_asset_id_format(self, client):
        """Invalid asset ID should be handled gracefully."""
        # Path traversal attempts are handled by URL routing
        # The path gets normalized before reaching the handler
        response = client.post("/api/assets/not-a-valid-uuid/estimate-key")

        # Should return 400 for invalid UUID or 404 for not found
        assert response.status_code in (400, 404)

"""Tests for jobs module."""
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from app.jobs import JobManager, Job, get_job_manager, set_job_manager
from app.models import AssetType, JobStatus


class TestJobManager:
    """Tests for JobManager class."""

    def test_create_job_returns_id(self, temp_dir):
        """create_job should return a job ID."""
        manager = JobManager()
        input_path = temp_dir / "test.mp4"
        input_path.touch()

        with patch("app.jobs.generate_id", return_value="test-job-id"), \
             patch("app.jobs.get_output_path", return_value=temp_dir / "output.webm"), \
             patch("app.jobs.get_log_path", return_value=temp_dir / "log.txt"), \
             patch("app.jobs.get_video_metadata") as mock_metadata, \
             patch("app.jobs.build_render_command", return_value=["echo", "test"]), \
             patch("threading.Thread") as mock_thread:

            mock_metadata.return_value = MagicMock(duration=10.0, has_audio=True)
            # Prevent background thread from actually running
            mock_thread.return_value.start = MagicMock()

            job_id = manager.create_job(
                asset_id="asset-123",
                input_path=input_path,
                asset_type=AssetType.VIDEO,
                hex_color="00FF00",
                similarity=0.4,
                blend=0.1,
                crf=24,
                include_audio=True
            )

            assert job_id == "test-job-id"
            mock_thread.assert_called_once()

    def test_get_job_returns_job(self):
        """get_job should return the job."""
        manager = JobManager()

        # Add a job directly
        job = Job(
            job_id="test-id",
            asset_id="asset-123",
            input_path=Path("/test/input.mp4"),
            asset_type=AssetType.VIDEO,
            hex_color="00FF00",
            similarity=0.4,
            blend=0.1
        )
        manager._jobs["test-id"] = job

        result = manager.get_job("test-id")
        assert result is not None
        assert result.job_id == "test-id"
        assert result.asset_id == "asset-123"

    def test_get_job_returns_none_for_missing(self):
        """get_job should return None for missing job."""
        manager = JobManager()
        result = manager.get_job("nonexistent-id")
        assert result is None

    def test_cancel_job_queued(self):
        """cancel_job should cancel a queued job."""
        manager = JobManager()

        job = Job(
            job_id="test-id",
            asset_id="asset-123",
            input_path=Path("/test/input.mp4"),
            asset_type=AssetType.VIDEO,
            hex_color="00FF00",
            similarity=0.4,
            blend=0.1,
            status=JobStatus.QUEUED
        )
        manager._jobs["test-id"] = job

        result = manager.cancel_job("test-id")
        assert result is True
        assert job.status == JobStatus.CANCELED
        assert job.message == "Canceled by user"
        assert job.finished_at is not None

    def test_cancel_job_running(self):
        """cancel_job should cancel a running job."""
        manager = JobManager()

        mock_process = MagicMock()
        mock_process.wait.return_value = None

        job = Job(
            job_id="test-id",
            asset_id="asset-123",
            input_path=Path("/test/input.mp4"),
            asset_type=AssetType.VIDEO,
            hex_color="00FF00",
            similarity=0.4,
            blend=0.1,
            status=JobStatus.RUNNING,
            process=mock_process
        )
        manager._jobs["test-id"] = job

        result = manager.cancel_job("test-id")
        assert result is True
        mock_process.terminate.assert_called_once()

    def test_cancel_job_already_done(self):
        """cancel_job should return False for completed job."""
        manager = JobManager()

        job = Job(
            job_id="test-id",
            asset_id="asset-123",
            input_path=Path("/test/input.mp4"),
            asset_type=AssetType.VIDEO,
            hex_color="00FF00",
            similarity=0.4,
            blend=0.1,
            status=JobStatus.DONE
        )
        manager._jobs["test-id"] = job

        result = manager.cancel_job("test-id")
        assert result is False
        assert job.status == JobStatus.DONE

    def test_cancel_job_nonexistent(self):
        """cancel_job should return False for nonexistent job."""
        manager = JobManager()
        result = manager.cancel_job("nonexistent-id")
        assert result is False


class TestJobManagerDependencyInjection:
    """Tests for JobManager dependency injection."""

    def test_get_job_manager_returns_singleton(self):
        """get_job_manager should return a singleton by default."""
        set_job_manager(None)  # Reset

        manager1 = get_job_manager()
        manager2 = get_job_manager()

        assert manager1 is manager2

    def test_set_job_manager_overrides_singleton(self):
        """set_job_manager should override the singleton."""
        custom_manager = JobManager()
        set_job_manager(custom_manager)

        result = get_job_manager()
        assert result is custom_manager

        # Cleanup
        set_job_manager(None)

    def test_set_job_manager_none_resets(self):
        """set_job_manager(None) should reset to default behavior."""
        custom_manager = JobManager()
        set_job_manager(custom_manager)
        set_job_manager(None)

        result = get_job_manager()
        assert result is not custom_manager


class TestJob:
    """Tests for Job dataclass."""

    def test_job_default_values(self):
        """Job should have correct default values."""
        job = Job(
            job_id="test-id",
            asset_id="asset-123",
            input_path=Path("/test/input.mp4"),
            asset_type=AssetType.VIDEO,
            hex_color="00FF00",
            similarity=0.4,
            blend=0.1
        )

        assert job.status == JobStatus.QUEUED
        assert job.progress == 0.0
        assert job.message is None
        assert job.started_at is None
        assert job.finished_at is None
        assert job.process is None
        assert job.log_lines == []

    def test_job_video_fields(self):
        """Job should accept video-specific fields."""
        job = Job(
            job_id="test-id",
            asset_id="asset-123",
            input_path=Path("/test/input.mp4"),
            asset_type=AssetType.VIDEO,
            hex_color="00FF00",
            similarity=0.4,
            blend=0.1,
            crf=24,
            include_audio=True
        )

        assert job.crf == 24
        assert job.include_audio is True

    def test_job_image_fields(self):
        """Job should work for image assets."""
        job = Job(
            job_id="test-id",
            asset_id="asset-123",
            input_path=Path("/test/input.png"),
            asset_type=AssetType.IMAGE,
            hex_color="00FF00",
            similarity=0.4,
            blend=0.1
        )

        assert job.asset_type == AssetType.IMAGE
        assert job.crf is None
        assert job.include_audio is False

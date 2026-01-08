"""Job management for render tasks."""
import subprocess
import threading
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from .ffmpeg_tools import (
    build_render_command,
    build_image_render_command,
    parse_progress,
    get_video_metadata,
)
from .models import AssetType, JobStatus
from .settings import get_logger
from .storage import get_output_path, get_log_path, generate_id

logger = get_logger(__name__)


@dataclass
class Job:
    """Render job state."""
    job_id: str
    asset_id: str
    input_path: Path
    asset_type: AssetType
    hex_color: str
    similarity: float
    blend: float
    crf: Optional[int] = None  # Video only
    include_audio: bool = False  # Video only
    status: JobStatus = JobStatus.QUEUED
    progress: float = 0.0
    message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    process: Optional[subprocess.Popen] = None
    log_lines: list[str] = field(default_factory=list)


class JobManager:
    """Manager for render jobs."""

    def __init__(self):
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def create_job(
        self,
        asset_id: str,
        input_path: Path,
        asset_type: AssetType,
        hex_color: str,
        similarity: float,
        blend: float,
        crf: Optional[int] = None,
        include_audio: bool = False
    ) -> str:
        """Create a new render job and start it in background."""
        job_id = generate_id()

        job = Job(
            job_id=job_id,
            asset_id=asset_id,
            input_path=input_path,
            asset_type=asset_type,
            hex_color=hex_color,
            similarity=similarity,
            blend=blend,
            crf=crf,
            include_audio=include_audio
        )

        with self._lock:
            self._jobs[job_id] = job

        logger.info(f"Job created: id={job_id}, asset={asset_id}, type={asset_type.value}")

        # Start render in background thread
        thread = threading.Thread(target=self._run_render, args=(job_id,), daemon=True)
        thread.start()

        return job_id

    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        with self._lock:
            return self._jobs.get(job_id)

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job."""
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False

            if job.status not in (JobStatus.QUEUED, JobStatus.RUNNING):
                return False

            if job.process:
                job.process.terminate()
                try:
                    job.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    job.process.kill()

            job.status = JobStatus.CANCELED
            job.finished_at = datetime.now()
            job.message = "Canceled by user"

        logger.info(f"Job canceled: id={job_id}")
        return True

    def _run_render(self, job_id: str) -> None:
        """Run the render process."""
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            job.status = JobStatus.RUNNING
            job.started_at = datetime.now()

        # Determine output extension based on asset type
        is_video = job.asset_type == AssetType.VIDEO
        output_ext = "webm" if is_video else "png"
        output_path = get_output_path(job_id, output_ext)
        log_path = get_log_path(job_id)

        try:
            if is_video:
                # Video rendering with progress tracking
                metadata = get_video_metadata(job.input_path)
                duration_ms = int(metadata.duration * 1000)

                cmd = build_render_command(
                    input_path=job.input_path,
                    output_path=output_path,
                    hex_color=job.hex_color,
                    similarity=job.similarity,
                    blend=job.blend,
                    crf=job.crf or 24,
                    include_audio=job.include_audio,
                    has_audio=metadata.has_audio
                )

                with self._lock:
                    job.log_lines.append(f"Command: {' '.join(cmd)}")

                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                with self._lock:
                    job.process = process

                # Read progress from stdout with proper resource management
                with open(log_path, "w") as log_file:
                    while True:
                        with self._lock:
                            if job.status == JobStatus.CANCELED:
                                break

                        line = process.stdout.readline()
                        if not line:
                            break

                        log_file.write(line)
                        log_file.flush()

                        out_time_ms = parse_progress(line.strip())
                        if out_time_ms is not None and duration_ms > 0:
                            progress = min(1.0, out_time_ms / duration_ms)
                            with self._lock:
                                job.progress = progress

                    # Wait for process to finish
                    process.wait()

                    # Capture stderr
                    stderr = process.stderr.read()
                    if stderr:
                        log_file.write("\n--- STDERR ---\n")
                        log_file.write(stderr)
            else:
                # Image rendering (instant, no progress tracking needed)
                cmd = build_image_render_command(
                    input_path=job.input_path,
                    output_path=output_path,
                    hex_color=job.hex_color,
                    similarity=job.similarity,
                    blend=job.blend
                )

                with self._lock:
                    job.log_lines.append(f"Command: {' '.join(cmd)}")

                # Run synchronously for images (very fast)
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                # Write log
                with open(log_path, "w") as log_file:
                    log_file.write(f"Command: {' '.join(cmd)}\n")
                    if result.stdout:
                        log_file.write(result.stdout)
                    if result.stderr:
                        log_file.write("\n--- STDERR ---\n")
                        log_file.write(result.stderr)

                # Set process return code for later check
                class FakeProcess:
                    def __init__(self, returncode):
                        self.returncode = returncode
                process = FakeProcess(result.returncode)

            # Read last log lines
            with open(log_path, "r") as f:
                all_lines = f.readlines()
                last_lines = [line.strip() for line in all_lines[-10:]]

            with self._lock:
                if job.status == JobStatus.CANCELED:
                    return

                if process.returncode == 0 and output_path.exists():
                    job.status = JobStatus.DONE
                    job.progress = 1.0
                    job.message = "Render completed successfully"
                    logger.info(f"Job completed: id={job_id}")
                else:
                    job.status = JobStatus.ERROR
                    job.message = f"FFmpeg exited with code {process.returncode}"
                    logger.error(f"Job failed: id={job_id}, returncode={process.returncode}")

                job.finished_at = datetime.now()
                job.log_lines = last_lines

        except subprocess.TimeoutExpired as e:
            logger.error(f"Job timed out: id={job_id}, timeout={e.timeout}s")
            with self._lock:
                job.status = JobStatus.ERROR
                job.message = f"Render timed out after {e.timeout} seconds"
                job.finished_at = datetime.now()
        except subprocess.SubprocessError as e:
            logger.error(f"Job subprocess error: id={job_id}, error={e}")
            with self._lock:
                job.status = JobStatus.ERROR
                job.message = f"Subprocess error: {e}"
                job.finished_at = datetime.now()
        except OSError as e:
            logger.error(f"Job filesystem error: id={job_id}, error={e}")
            with self._lock:
                job.status = JobStatus.ERROR
                job.message = f"File system error: {e}"
                job.finished_at = datetime.now()
        except Exception as e:
            # Capture full traceback for unexpected errors
            error_details = traceback.format_exc()
            logger.error(f"Job unexpected error: id={job_id}, error={e}\n{error_details}")
            with self._lock:
                job.status = JobStatus.ERROR
                job.message = f"Unexpected error: {e}"
                job.log_lines.append(f"Error traceback:\n{error_details}")
                job.finished_at = datetime.now()


# Global job manager instance (default singleton for production)
_job_manager: Optional[JobManager] = None


def get_job_manager() -> JobManager:
    """Get the global JobManager instance.

    This function supports dependency injection for testing.
    Call set_job_manager() to override with a mock for tests.
    """
    global _job_manager
    if _job_manager is None:
        _job_manager = JobManager()
    return _job_manager


def set_job_manager(manager: Optional[JobManager]) -> None:
    """Set a custom JobManager instance (for testing).

    Pass None to reset to default behavior.
    """
    global _job_manager
    _job_manager = manager


# Backwards compatibility alias
job_manager = get_job_manager()

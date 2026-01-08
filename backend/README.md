# AutoChroma Mini Studio - Backend

FastAPI backend for video chromakey transparency processing.

## API Endpoints

### System

- `GET /api/probe` - Check if ffmpeg/ffprobe are available

### Assets

- `POST /api/assets` - Upload a video file (multipart/form-data)
- `POST /api/assets/{asset_id}/estimate-key` - Estimate background key color
- `POST /api/assets/{asset_id}/preview` - Generate preview PNG with chromakey
- `POST /api/assets/{asset_id}/render` - Start render job

### Jobs

- `GET /api/jobs/{job_id}` - Get job status and progress
- `POST /api/jobs/{job_id}/cancel` - Cancel a running job
- `GET /api/jobs/{job_id}/download` - Download rendered output

## Data Directory

The backend stores data in `.data/`:

```
.data/
├── assets/{asset_id}/     # Uploaded video files
│   └── input.{ext}
├── outputs/{job_id}/      # Rendered output files
│   └── out.webm
├── previews/{preview_id}/ # Preview images
│   └── preview.png
└── logs/{job_id}.log      # Render logs
```

## Development

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

API docs available at http://localhost:8000/docs

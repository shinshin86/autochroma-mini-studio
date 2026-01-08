# AutoChroma Mini Studio

![Demo](./assets/demo.png)

A local web app that automatically estimates background color and exports transparent (alpha) videos (WebM VP9) and images (PNG) using ffmpeg's chromakey filter.

[日本語版 README](./README.ja.md)

## Requirements

- **Python 3.11+**
- **Node.js 18+** (20+ recommended)
- **uv** (Python package manager)
- **ffmpeg** and **ffprobe** available in PATH

### Installing ffmpeg

**macOS (Homebrew):**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update && sudo apt install ffmpeg
```

**Windows:**
1. Download from [ffmpeg official site](https://ffmpeg.org/download.html)
2. Extract to a location of your choice
3. Add the ffmpeg bin folder to your PATH environment variable

## Getting Started

### One-Command Launch (Recommended)

**macOS / Linux:**
```bash
./start.sh
```

**Windows:**
```cmd
start.bat
```

This will automatically install dependencies and start both servers.

### Manual Launch

**Backend:**
```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### Usage

Open http://localhost:5173 in your browser

## Running Tests

**Backend:**
```bash
cd backend
uv run pytest
```

**Frontend:**
```bash
cd frontend
npm run test:run
```

## How to Use

1. **Select File**: Upload a video or image via drag & drop or click
2. **Estimate Background Color**: Click "Auto Estimate" or manually specify the key color
3. **Adjust Parameters**: Fine-tune similarity, blend, and CRF values (CRF is video-only)
4. **Preview**: Check the transparency result with a preview image
5. **Export**: Click "Start Export" to generate a transparent file
   - Video → WebM VP9 with alpha
   - Image → PNG with alpha
6. **Download**: Download the completed file

## Troubleshooting

### `/api/probe` returns ok=false

ffmpeg or ffprobe is not in your PATH.

```bash
# Check installation
which ffmpeg
which ffprobe

# Or
ffmpeg -version
ffprobe -version
```

If not installed, follow the installation instructions above.

### ffmpeg PATH issues on Windows

1. Open System Environment Variables
2. Add the ffmpeg bin folder path to PATH variable
3. Restart Command Prompt

Example: Add `C:\ffmpeg\bin` to PATH

### Rendering takes a long time for large videos

This is normal. WebM VP9 + alpha encoding is computationally intensive. Processing time increases with video length and resolution. You can monitor progress via the progress bar.

### CORS errors

Make sure the backend is running. The frontend connects to `http://localhost:8000` by default.

## Project Structure

```
autochroma-mini-studio/
├── README.md
├── README.ja.md      # Japanese README
├── LICENSE
├── .gitignore
├── start.sh          # One-command launch (macOS/Linux)
├── start.bat         # One-command launch (Windows)
├── backend/
│   ├── README.md
│   ├── pyproject.toml
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── settings.py
│   │   ├── models.py
│   │   ├── storage.py
│   │   ├── ffmpeg_tools.py
│   │   └── jobs.py
│   └── tests/
│       ├── conftest.py
│       ├── test_api.py
│       ├── test_ffmpeg_tools.py
│       ├── test_jobs.py
│       └── test_storage.py
└── frontend/
    ├── .env.example
    ├── package.json
    └── src/
        ├── test/
        │   └── setup.ts
        ├── api/
        │   ├── client.ts
        │   ├── client.test.ts
        │   └── types.ts
        ├── components/
        │   ├── FileStep.tsx
        │   ├── FileStep.test.tsx
        │   ├── KeySettings.tsx
        │   ├── KeySettings.test.tsx
        │   ├── PreviewPane.tsx
        │   ├── RenderPane.tsx
        │   └── LogPane.tsx
        ├── App.tsx
        ├── main.tsx
        └── index.css
```

## License

MIT License

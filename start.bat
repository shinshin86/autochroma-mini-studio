@echo off
REM AutoChroma Mini Studio - Development Server Launcher
REM Usage: start.bat

echo AutoChroma Mini Studio
echo =========================

REM Check dependencies
echo.
echo Checking dependencies...

where uv >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: uv is not installed
    echo Install it from: https://docs.astral.sh/uv/getting-started/installation/
    exit /b 1
)

where node >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: Node.js is not installed
    exit /b 1
)

where ffmpeg >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Warning: ffmpeg is not installed
    echo Some features may not work
)

REM Install dependencies if needed
echo.
echo Setting up backend...
cd /d "%~dp0backend"
call uv sync

echo.
echo Setting up frontend...
cd /d "%~dp0frontend"
if not exist "node_modules" (
    call npm install
)

REM Start servers
echo.
echo Starting servers...
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo.
echo Close this window to stop both servers
echo.

REM Start backend in new window
cd /d "%~dp0backend"
start "AutoChroma Backend" cmd /c "uv run uvicorn app.main:app --reload --port 8000"

REM Start frontend in current window
cd /d "%~dp0frontend"
call npm run dev

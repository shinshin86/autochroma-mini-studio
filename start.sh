#!/bin/bash

# AutoChroma Mini Studio - Development Server Launcher
# Usage: ./start.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}AutoChroma Mini Studio${NC}"
echo "========================="

# Check dependencies
echo -e "\n${YELLOW}Checking dependencies...${NC}"

if ! command -v uv &> /dev/null; then
    echo -e "${RED}Error: uv is not installed${NC}"
    echo "Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js is not installed${NC}"
    exit 1
fi

if ! command -v ffmpeg &> /dev/null; then
    echo -e "${RED}Warning: ffmpeg is not installed${NC}"
    echo "Some features may not work"
fi

# Install dependencies if needed
echo -e "\n${YELLOW}Setting up backend...${NC}"
cd "$SCRIPT_DIR/backend"
uv sync

echo -e "\n${YELLOW}Setting up frontend...${NC}"
cd "$SCRIPT_DIR/frontend"
if [ ! -d "node_modules" ]; then
    npm install
fi

# Start servers
echo -e "\n${GREEN}Starting servers...${NC}"
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Trap to kill both processes on exit
trap 'kill 0' EXIT

# Start backend in background
cd "$SCRIPT_DIR/backend"
uv run uvicorn app.main:app --reload --port 8000 &

# Start frontend in foreground
cd "$SCRIPT_DIR/frontend"
npm run dev

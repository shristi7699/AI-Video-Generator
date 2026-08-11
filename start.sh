#!/bin/bash

# Ensure script stops on first error
set -e

echo "Starting AI-Video-Generator..."

# Check if venv exists, if not create it
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

# Create working directory if it doesn't exist
mkdir -p .working_dir

# Start the server
echo "Starting FastAPI server..."
uvicorn server:app --host 0.0.0.0 --port 8000 --reload

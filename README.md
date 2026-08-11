# AI Text-to-Video Generator

A self-hosted, FastAPI-based AI text-to-video generator with a web UI.

## Features
- **Simple Video Mode**: Generate a single video clip from a prompt.
- **Creative Video Mode**: Turn an idea into a multi-scene scripted video with AI narration and subtitles.
- **Real-time Progress**: View generation progress live via WebSockets.
- **Task Persistence**: Tasks survive server restarts.

## Prerequisites
- Python 3.10+
- `ffmpeg` installed and available in system PATH.
- [Replicate](https://replicate.com/) API Token (for video generation).
- [Anthropic](https://anthropic.com/) API Key (for Claude script generation in Creative Mode).

## Setup Instructions

1. Clone or download this repository.
2. Copy `.env.example` to `.env` and add your API keys:
   ```bash
   cp .env.example .env
   # Edit .env and add keys
   ```
3. Run the start script:
   ```bash
   bash start.sh
   ```
4. Open the web UI in your browser: `http://localhost:8000`

## Architecture
- **Backend**: FastAPI (Python), serving REST and WebSocket endpoints.
- **Frontend**: Vanilla HTML/JS with Tailwind CSS (CDN).
- **Video Generation**: Replicate API (default model: `minimax/video-01`).
- **Script Generation**: Anthropic Claude API.
- **Text-to-Speech**: `edge-tts` (Free, Microsoft Edge TTS).
- **Video Processing**: `ffmpeg` directly for compositing and subtitle burn-in.

## Extending It
To add new modes or models:
1. Update `models/task.py` with new request schemas.
2. Add a new pipeline in `core/pipelines/`.
3. Create new endpoints in `server.py`.
4. Update the frontend `index.html` to support the new mode.
You can also change the default Replicate video model in `core/config.py`.

## Credits & APIs Used
This project relies on the following incredible tools and APIs:
- **[Replicate](https://replicate.com/)**: Providing the serverless infrastructure for AI video models (e.g., Minimax Video-01).
- **[Anthropic Claude](https://www.anthropic.com/)**: Powering the "Creative Mode" script generation to turn ideas into structured scenes.
- **[edge-tts](https://github.com/rany2/edge-tts)**: An open-source Python module to use Microsoft Edge's online text-to-speech service without needing an API key.
- **[FFmpeg](https://ffmpeg.org/)**: The industry standard for video and audio processing, used here for stitching scenes and burning in subtitles.

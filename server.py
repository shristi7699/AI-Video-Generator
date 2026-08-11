import os
import uuid
import asyncio
import subprocess
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.config import config
from models.task import Task, SimpleVideoRequest, CreativeVideoRequest, TaskStatus
from core.task_manager import task_manager
from core.pipelines.simple_video import run_simple_video_pipeline
from core.pipelines.creative_video import run_creative_video_pipeline

app = FastAPI(title="AI Video Generator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Check for ffmpeg on startup
@app.on_event("startup")
async def startup_event():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print("FFmpeg is installed and accessible.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("\n" + "="*50)
        print("CRITICAL ERROR: FFmpeg is not installed or not in PATH.")
        print("Please install ffmpeg before running the server.")
        print("="*50 + "\n")
        os._exit(1) # Silent fail gracefully handled with clear message

# Serve static files for frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def serve_index():
    return FileResponse("static/index.html")

class ConfigUpdate(BaseModel):
    replicate_token: str
    anthropic_key: str

@app.post("/api/config")
async def update_config(c: ConfigUpdate):
    config.REPLICATE_API_TOKEN = c.replicate_token
    config.ANTHROPIC_API_KEY = c.anthropic_key
    return {"status": "success"}

@app.get("/api/config")
async def get_config():
    return {
        "replicate_configured": bool(config.REPLICATE_API_TOKEN),
        "anthropic_configured": bool(config.ANTHROPIC_API_KEY)
    }

@app.post("/api/tasks/simple")
async def create_simple_task(req: SimpleVideoRequest):
    task_id = str(uuid.uuid4())
    task = Task(id=task_id, mode="simple")
    await task_manager.create_task(task)
    # Start pipeline in background
    asyncio.create_task(run_simple_video_pipeline(task_id, req.prompt))
    return {"task_id": task_id}

@app.post("/api/tasks/creative")
async def create_creative_task(req: CreativeVideoRequest):
    task_id = str(uuid.uuid4())
    task = Task(id=task_id, mode="creative")
    await task_manager.create_task(task)
    # Start pipeline in background
    asyncio.create_task(run_creative_video_pipeline(task_id, req.idea))
    return {"task_id": task_id}

@app.get("/api/tasks")
async def list_tasks():
    tasks = await task_manager.get_all_tasks()
    return tasks

@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str):
    task = await task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.get("/api/video/{task_id}")
async def get_video(task_id: str):
    task = await task_manager.get_task(task_id)
    if not task or not task.final_video_path or not os.path.exists(task.final_video_path):
        raise HTTPException(status_code=404, detail="Video not found")
    return FileResponse(task.final_video_path, media_type="video/mp4")

# WebSocket for real-time progress
@app.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    await websocket.accept()
    try:
        last_progress = None
        last_step = None
        while True:
            task = await task_manager.get_task(task_id)
            if not task:
                await websocket.send_json({"error": "Task not found"})
                break
                
            if task.progress != last_progress or task.step != last_step or task.status in (TaskStatus.DONE, TaskStatus.FAILED):
                await websocket.send_json(task.model_dump())
                last_progress = task.progress
                last_step = task.step
                
            if task.status in (TaskStatus.DONE, TaskStatus.FAILED):
                break
                
            await asyncio.sleep(1) # Poll interval for WebSocket
    except WebSocketDisconnect:
        pass

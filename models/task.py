from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"

class Scene(BaseModel):
    id: int
    narration: str = Field(description="The spoken narration for this scene")
    video_prompt: str = Field(description="The text-to-video prompt to generate the visual for this scene")
    video_url: Optional[str] = None
    audio_path: Optional[str] = None
    srt_path: Optional[str] = None
    video_path: Optional[str] = None # Downloaded video path
    final_scene_path: Optional[str] = None # Scene with audio and subtitles burned in

class Task(BaseModel):
    id: str
    mode: str = Field(description="Either 'simple' or 'creative'")
    status: TaskStatus = TaskStatus.PENDING
    step: str = "Initializing"
    progress: float = 0.0
    scenes: List[Scene] = []
    final_video_path: Optional[str] = None
    error_message: Optional[str] = None

class SimpleVideoRequest(BaseModel):
    prompt: str

class CreativeVideoRequest(BaseModel):
    idea: str
    scene_count: int = Field(default=5, le=20)
    duration_per_scene: int = Field(default=5, le=10)
    enable_character_consistency: bool = True

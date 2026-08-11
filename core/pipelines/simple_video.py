import os
import httpx
import aiofiles
from models.task import Task, TaskStatus
from core.api.video_api import generate_video
from core.api.rate_limiter import video_rate_limiter
from core.task_manager import task_manager

async def download_file(url: str, dest_path: str):
    async with httpx.AsyncClient(follow_redirects=True) as client:
        async with client.stream("GET", url) as response:
            response.raise_for_status()
            async with aiofiles.open(dest_path, 'wb') as f:
                async for chunk in response.aiter_bytes():
                    await f.write(chunk)

async def run_simple_video_pipeline(task_id: str, prompt: str):
    task = await task_manager.get_task(task_id)
    if not task:
        return

    try:
        task.step = "Generating Video"
        task.status = TaskStatus.RUNNING
        await task_manager.update_task(task)

        # Rate limited API call
        async with video_rate_limiter:
            video_url = await generate_video(prompt)
            task.progress = 0.5
            await task_manager.update_task(task)

        task.step = "Downloading Video"
        await task_manager.update_task(task)
        
        task_dir = os.path.join(".working_dir", task_id)
        video_path = os.path.join(task_dir, "final.mp4")
        
        await download_file(video_url, video_path)

        task.final_video_path = video_path
        task.progress = 1.0
        task.step = "Completed"
        task.status = TaskStatus.DONE
        await task_manager.update_task(task)

    except Exception as e:
        task.status = TaskStatus.FAILED
        task.error_message = str(e)
        await task_manager.update_task(task)

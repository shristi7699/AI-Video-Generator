import json
import os
import asyncio
from typing import Dict, List, Optional
from models.task import Task
from core.config import config

class TaskManager:
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.lock = asyncio.Lock()
        self._load_from_disk()

    def _get_task_dir(self, task_id: str) -> str:
        d = os.path.join(config.WORKING_DIR, task_id)
        os.makedirs(d, exist_ok=True)
        return d

    def _get_task_file(self, task_id: str) -> str:
        return os.path.join(self._get_task_dir(task_id), "task.json")

    def _load_from_disk(self):
        if not os.path.exists(config.WORKING_DIR):
            return
        for task_id in os.listdir(config.WORKING_DIR):
            task_file = os.path.join(config.WORKING_DIR, task_id, "task.json")
            if os.path.isfile(task_file):
                try:
                    with open(task_file, "r") as f:
                        data = json.load(f)
                        self.tasks[task_id] = Task(**data)
                except Exception as e:
                    print(f"Error loading task {task_id}: {e}")

    async def _save_to_disk(self, task: Task):
        try:
            task_file = self._get_task_file(task.id)
            with open(task_file, "w") as f:
                json.dump(task.model_dump(), f, indent=2)
        except Exception as e:
            print(f"Error saving task {task.id}: {e}")

    async def get_task(self, task_id: str) -> Optional[Task]:
        async with self.lock:
            return self.tasks.get(task_id)

    async def get_all_tasks(self) -> List[Task]:
        async with self.lock:
            return list(self.tasks.values())

    async def create_task(self, task: Task):
        async with self.lock:
            self.tasks[task.id] = task
            await self._save_to_disk(task)

    async def update_task(self, task: Task):
        async with self.lock:
            self.tasks[task.id] = task
            await self._save_to_disk(task)

task_manager = TaskManager()

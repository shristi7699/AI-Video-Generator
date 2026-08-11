import os
import asyncio
from models.task import Task, TaskStatus, Scene
from core.api.video_api import generate_video
from core.api.llm_api import generate_script
from core.api.rate_limiter import video_rate_limiter
from core.audio.tts import generate_audio
from core.audio.subtitle import generate_srt
from core.compositor.concatenator import process_scene, concatenate_videos, burn_subtitles
from core.task_manager import task_manager
from core.pipelines.simple_video import download_file

async def process_single_scene(scene: Scene, task_dir: str, reference_image_url: str = None):
    """Processes a single scene: generates video, downloads it, and generates TTS."""
    # 1. Generate and download video
    async with video_rate_limiter:
        video_url = await generate_video(scene.video_prompt, reference_image_url=reference_image_url)
    scene.video_url = video_url
    
    scene.video_path = os.path.join(task_dir, f"scene_{scene.id}_raw.mp4")
    await download_file(video_url, scene.video_path)
    
    # 2. Generate audio and SRT
    scene.audio_path = os.path.join(task_dir, f"scene_{scene.id}.mp3")
    word_json_path = os.path.join(task_dir, f"scene_{scene.id}_words.json")
    await generate_audio(scene.narration, scene.audio_path, word_json_path)
    
    scene.srt_path = os.path.join(task_dir, f"scene_{scene.id}.srt")
    generate_srt(word_json_path, scene.srt_path)
    
    # 3. Combine raw video and audio for this scene
    scene_combined_path = os.path.join(task_dir, f"scene_{scene.id}_combined.mp4")
    await process_scene(scene.video_path, scene.audio_path, scene_combined_path)
    
    # 4. Burn subtitles into this scene
    scene.final_scene_path = os.path.join(task_dir, f"scene_{scene.id}_final.mp4")
    await burn_subtitles(scene_combined_path, scene.srt_path, scene.final_scene_path)
    
    return scene

async def run_creative_video_pipeline(task_id: str, idea: str):
    task = await task_manager.get_task(task_id)
    if not task:
        return
        
    task_dir = os.path.join(".working_dir", task_id)
    reference_image_url = None
    character_description = ""

    try:
        # Step 1: Script Generation
        task.step = "Generating Script (LLM)"
        task.status = TaskStatus.RUNNING
        await task_manager.update_task(task)
        
        # Access the new scene_count field (default to 5 if not set by an old request)
        scene_count = getattr(task, 'scene_count', 5)
        
        script_data = await generate_script(idea, scene_count)
        character_description = script_data.get("character_description", "")
        scene_dicts = script_data.get("scenes", [])
        
        # Step 1.5: Character Consistency Image Generation
        if getattr(task, 'enable_character_consistency', True) and character_description:
            task.step = "Generating Character Reference Image"
            await task_manager.update_task(task)
            try:
                from core.api.image_api import generate_reference_image
                reference_image_url = await generate_reference_image(character_description)
            except Exception as e:
                print(f"Warning: Character reference image failed: {e}")
                task.error_message = "Warning: character reference image failed, continuing with text-only consistency."
                # Don't crash, continue without reference image
                reference_image_url = None

        for i, s_dict in enumerate(scene_dicts):
            # Prepend character description for text-only consistency
            enhanced_prompt = f"Character: {character_description}. Scene: {s_dict['video_prompt']}" if character_description else s_dict["video_prompt"]
            task.scenes.append(Scene(
                id=i, 
                narration=s_dict["narration"], 
                video_prompt=enhanced_prompt
            ))
            
        task.progress = 0.1
        task.step = "Generating Scenes"
        await task_manager.update_task(task)
        
        # Step 2: Process scenes concurrently
        async def process_and_update(scene, total_scenes):
            try:
                res = await process_single_scene(scene, task_dir, reference_image_url=reference_image_url)
                task.progress += (0.7 / total_scenes) # Allocate 70% of progress to scenes
                await task_manager.update_task(task)
                return res
            except Exception as e:
                raise Exception(f"Scene {scene.id} failed: {str(e)}")
                
        processed_scenes = await asyncio.gather(
            *(process_and_update(scene, len(task.scenes)) for scene in task.scenes)
        )
        task.scenes = list(processed_scenes)
        
        # Step 3: Concatenate scenes
        task.step = "Stitching Video"
        await task_manager.update_task(task)
        
        scene_video_paths = [s.final_scene_path for s in task.scenes]
        stitched_video_path = os.path.join(task_dir, "final.mp4")
        await concatenate_videos(scene_video_paths, stitched_video_path)
        
        task.final_video_path = stitched_video_path
        task.progress = 1.0
        task.step = "Completed"
        task.status = TaskStatus.DONE
        await task_manager.update_task(task)

    except Exception as e:
        task.status = TaskStatus.FAILED
        task.error_message = str(e)
        await task_manager.update_task(task)

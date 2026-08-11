import asyncio
import subprocess
import os

async def process_scene(video_path: str, audio_path: str, output_path: str):
    """
    Combines video and audio for a single scene.
    Loops the video if it's shorter than the audio, and cuts it to the audio length.
    """
    # -stream_loop -1 loops the input infinitely
    # -shortest finishes encoding when the shortest stream ends (which will be the audio, since video is infinite)
    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1", "-i", video_path,
        "-i", audio_path,
        "-c:v", "libx264",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        output_path
    ]
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    
    if process.returncode != 0:
        raise Exception(f"FFmpeg process_scene failed: {stderr.decode()}")

async def concatenate_videos(video_paths: list[str], output_path: str):
    """
    Concatenates multiple video files into one.
    """
    # Create a concat list file
    list_file_path = f"{output_path}.txt"
    with open(list_file_path, "w") as f:
        for vp in video_paths:
            # Need to escape paths or ensure they are absolute/relative properly
            f.write(f"file '{os.path.abspath(vp)}'\n")
            
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", list_file_path,
        "-c", "copy",
        output_path
    ]
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    
    # Cleanup list file
    if os.path.exists(list_file_path):
        os.remove(list_file_path)
        
    if process.returncode != 0:
        raise Exception(f"FFmpeg concat failed: {stderr.decode()}")

async def burn_subtitles(video_path: str, srt_path: str, output_path: str):
    """
    Burns SRT subtitles into the video.
    """
    # FFmpeg requires the subtitle path to be formatted in a specific way for the filter
    # Escaping for Windows/Linux path differences
    escaped_srt_path = os.path.abspath(srt_path).replace('\\', '/').replace(':', '\\:')
    
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", f"subtitles={escaped_srt_path}:force_style='FontSize=24,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=0'",
        "-c:a", "copy",
        output_path
    ]
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    
    if process.returncode != 0:
        raise Exception(f"FFmpeg burn_subtitles failed: {stderr.decode()}")

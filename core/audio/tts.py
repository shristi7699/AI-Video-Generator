import os
import json
import edge_tts

async def generate_audio(text: str, output_audio_path: str, output_json_path: str, voice: str = "en-US-AriaNeural"):
    """
    Generates TTS audio and saves word boundary data to a JSON file.
    """
    communicate = edge_tts.Communicate(text, voice)
    
    word_boundaries = []
    
    with open(output_audio_path, "wb") as audio_file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                word_boundaries.append({
                    "text": chunk["text"],
                    "offset": chunk["offset"],
                    "duration": chunk["duration"]
                })
                
    with open(output_json_path, "w") as json_file:
        json.dump(word_boundaries, json_file, indent=2)

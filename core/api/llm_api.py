import json
import anthropic
from typing import List, Dict
from core.config import config

async def generate_script(idea: str, scene_count: int = 5) -> Dict:
    """
    Calls Anthropic Claude to generate a script with narration and video prompts.
    Returns a dictionary with 'character_description' and 'scenes'.
    """
    if not config.ANTHROPIC_API_KEY:
        raise ValueError("Anthropic API key is missing")

    client = anthropic.AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)
    
    system_prompt = f"""You are an expert video director and scriptwriter.
The user will give you a video idea. You must break it down into a logical sequence of EXACTLY {scene_count} short scenes.
You must also invent a primary character for the video.

Provide the following:
1. `character_description`: A detailed physical description of the primary character (e.g., "A young woman with curly red hair, wearing a green jacket and silver rimmed glasses, freckles on her nose").
2. `scenes`: A list of scenes. For each scene, provide:
   - `narration`: The exact spoken text for the voiceover.
   - `video_prompt`: A detailed prompt for a text-to-video AI model describing what is visually happening in the scene. 

You MUST respond ONLY with a valid JSON object. 
Example format:
{{
  "character_description": "A young woman with curly red hair, green jacket",
  "scenes": [
    {{
      "narration": "Welcome to the future of AI.",
      "video_prompt": "A futuristic city with flying cars, cyberpunk style, neon lights, 4k, hyperrealistic"
    }}
  ]
}}
Do not include markdown blocks, just the raw JSON object."""

    message = await client.messages.create(
        model="claude-3-haiku-20240307", # Fast and cheap model for this task
        max_tokens=1024,
        temperature=0.7,
        system=system_prompt,
        messages=[
            {"role": "user", "content": idea}
        ]
    )
    
    response_text = message.content[0].text
    
    # Clean up response if the LLM added markdown block (e.g., ```json ... ```)
    response_text = response_text.strip()
    if response_text.startswith("```json"):
        response_text = response_text[7:]
    if response_text.startswith("```"):
        response_text = response_text[3:]
    if response_text.endswith("```"):
        response_text = response_text[:-3]
    
    try:
        response_json = json.loads(response_text.strip())
        if not isinstance(response_json, dict) or "scenes" not in response_json:
            raise ValueError("LLM did not return a valid JSON object with 'scenes'")
        return response_json
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse LLM JSON response: {response_text}") from e

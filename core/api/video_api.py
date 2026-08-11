import asyncio
import httpx
from core.config import config

async def generate_video(prompt: str, model_slug: str = None, reference_image_url: str = None) -> str:
    """
    Submits a video generation task to Replicate and polls until done.
    Returns the URL of the generated video.
    """
    if not config.REPLICATE_API_TOKEN:
        raise ValueError("Replicate API token is missing")

    model_slug = model_slug or config.DEFAULT_VIDEO_MODEL
    
    headers = {
        "Authorization": f"Token {config.REPLICATE_API_TOKEN}",
        "Content-Type": "application/json",
    }
    
    # We use the generic models predictions endpoint
    # Format for model_slug is typically "owner/name" or "owner/name:version"
    # To support both, it's safer to use the hardware/model predictions endpoint if no version is provided
    # Replicate API format for models: /v1/models/{model_owner}/{model_name}/predictions
    
    parts = model_slug.split("/")
    if len(parts) != 2:
        raise ValueError("Model slug must be in the format 'owner/name'")
    owner, name = parts

    submit_url = f"https://api.replicate.com/v1/models/{owner}/{name}/predictions"
    
    # Default parameters, might need adjustment based on the specific model
    payload = {
        "input": {
            "prompt": prompt
        }
    }
    
    if reference_image_url:
        payload["input"]["first_frame_image"] = reference_image_url

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Submit the job
        response = await client.post(submit_url, headers=headers, json=payload)
        
        if response.status_code != 201:
            raise Exception(f"Failed to submit to Replicate: {response.text}")
            
        prediction = response.json()
        get_url = prediction["urls"]["get"]
        
        # 2. Poll for completion
        while True:
            await asyncio.sleep(5)  # Poll every 5 seconds
            poll_resp = await client.get(get_url, headers=headers)
            if poll_resp.status_code != 200:
                raise Exception(f"Failed to poll Replicate: {poll_resp.text}")
                
            status_data = poll_resp.json()
            status = status_data["status"]
            
            if status == "succeeded":
                # Replicate usually returns output as a string (URL) or list of strings
                output = status_data.get("output")
                if isinstance(output, list) and len(output) > 0:
                    return output[0]
                elif isinstance(output, str):
                    return output
                else:
                    raise Exception(f"Unexpected output format from Replicate: {output}")
            elif status == "failed":
                error = status_data.get("error", "Unknown error")
                raise Exception(f"Video generation failed on Replicate: {error}")
            elif status == "canceled":
                raise Exception("Video generation was canceled")
            # If status is starting or processing, continue polling

import httpx
from core.config import config

async def generate_reference_image(character_description: str) -> str:
    """
    Calls Replicate's flux-schnell model to generate a character reference image.
    Returns the URL of the generated image.
    """
    if not config.REPLICATE_API_TOKEN:
        raise ValueError("Replicate API token is missing")

    # Replicate endpoint for predictions
    submit_url = "https://api.replicate.com/v1/models/black-forest-labs/flux-schnell/predictions"
    
    headers = {
        "Authorization": f"Token {config.REPLICATE_API_TOKEN}",
        "Content-Type": "application/json",
        "Prefer": "wait" # Wait for the prediction to finish
    }
    
    # Prefixing the prompt to ensure a good character reference shot
    prompt = f"A clear, well-lit portrait shot of: {character_description}. Consistent character reference sheet style, neutral background, high resolution, highly detailed."
    
    payload = {
        "input": {
            "prompt": prompt,
            "go_fast": True,
            "megapixels": "1",
            "num_outputs": 1,
            "output_format": "webp",
            "output_quality": 80,
            "aspect_ratio": "16:9"
        }
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(submit_url, headers=headers, json=payload)
        
        if response.status_code not in (200, 201):
            raise Exception(f"Failed to submit image generation to Replicate: {response.text}")
            
        prediction = response.json()
        
        if prediction.get("status") == "failed":
            raise Exception(f"Image generation failed on Replicate: {prediction.get('error')}")
            
        # If 'Prefer: wait' worked and it's already succeeded
        if prediction.get("status") == "succeeded":
             output = prediction.get("output")
             if isinstance(output, list) and len(output) > 0:
                 return output[0]
             elif isinstance(output, str):
                 return output
                 
        # If it didn't wait, poll it (Flux Schnell is very fast, usually takes < 5s)
        import asyncio
        get_url = prediction["urls"]["get"]
        while True:
            await asyncio.sleep(2)
            poll_resp = await client.get(get_url, headers=headers)
            if poll_resp.status_code != 200:
                raise Exception(f"Failed to poll Replicate image: {poll_resp.text}")
                
            status_data = poll_resp.json()
            status = status_data["status"]
            
            if status == "succeeded":
                output = status_data.get("output")
                if isinstance(output, list) and len(output) > 0:
                    return output[0]
                elif isinstance(output, str):
                    return output
            elif status == "failed":
                raise Exception(f"Image generation failed: {status_data.get('error')}")
            elif status == "canceled":
                raise Exception("Image generation was canceled")

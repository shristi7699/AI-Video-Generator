import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Module-level variables for backward compatibility
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

class Config:
    REPLICATE_API_TOKEN = REPLICATE_API_TOKEN
    ANTHROPIC_API_KEY = ANTHROPIC_API_KEY
    
    # You can swap this with any Replicate text-to-video model slug
    # E.g., 'ali-vilab/i2vgen-xl', 'stability-ai/stable-video-diffusion'
    # 'minimax/video-01' is lightweight and fast for testing.
    DEFAULT_VIDEO_MODEL = "minimax/video-01" 
    
    # Directory to store intermediate files and task state
    WORKING_DIR = ".working_dir"

    @classmethod
    def setup(cls):
        if not os.path.exists(cls.WORKING_DIR):
            os.makedirs(cls.WORKING_DIR, exist_ok=True)

config = Config()
config.setup()

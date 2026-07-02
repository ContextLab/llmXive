"""Configuration management for the project."""
import os
from pathlib import Path
from dotenv import load_dotenv

def load_env():
    """
    Load environment variables from .env file.
    
    Raises:
        ValueError: If MP_API_KEY is missing.
    """
    # Find .env file in project root
    project_root = Path(__file__).resolve().parent.parent
    env_path = project_root / ".env"
    
    if env_path.exists():
        load_dotenv(env_path)
    else:
        # Try current directory
        load_dotenv()

    api_key = os.getenv("MP_API_KEY")
    if not api_key or api_key == "placeholder":
        raise ValueError("MP_API_KEY is missing or not set in environment. Please set it in .env file.")
    
    return {
        "mp_api_key": api_key,
        "project_root": project_root
    }

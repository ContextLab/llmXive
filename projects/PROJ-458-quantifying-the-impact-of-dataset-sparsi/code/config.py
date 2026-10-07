"""
Configuration module for the project.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

def load_env():
    """
    Load environment variables from .env file.
    Raises an error if MP_API_KEY is missing.
    """
    env_path = Path(__file__).parent / '.env'
    load_dotenv(dotenv_path=env_path)
    
    mp_api_key = os.getenv('MP_API_KEY')
    if not mp_api_key:
        raise EnvironmentError(
            "MP_API_KEY is missing from environment. "
            "Please set it in the .env file or export it in your shell."
        )
    return mp_api_key

# Additional configuration constants can be added here
DATA_ROOT = Path(__file__).parent.parent / 'data'
CODE_ROOT = Path(__file__).parent
SPECS_ROOT = Path(__file__).parent.parent / 'specs'
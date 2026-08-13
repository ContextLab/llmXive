"""
T009: Environment configuration loader.
Reads from .env file and provides typed access to configuration values.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load .env file
def load_config(env_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from .env file.
    
    Args:
        env_path: Optional path to .env file (default: .env in project root)
    
    Returns:
        Dictionary of configuration values
    """
    if env_path is None:
        env_path = Path(__file__).parent.parent.parent / ".env"
    
    if not os.path.exists(env_path):
        logger.warning(f".env file not found at {env_path}")
        return {}
    
    load_dotenv(env_path)
    return {
        "MODEL_PATH": os.getenv("MODEL_PATH"),
        "DATASET_ID": os.getenv("DATASET_ID"),
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
        "OUTPUT_DIR": os.getenv("OUTPUT_DIR", "data/processed")
    }

def get_model_path() -> Optional[str]:
    """Get MODEL_PATH from environment."""
    return os.getenv("MODEL_PATH")

def get_dataset_id() -> Optional[str]:
    """Get DATASET_ID from environment."""
    return os.getenv("DATASET_ID")

def get_log_level() -> int:
    """Get LOG_LEVEL from environment, defaulting to INFO."""
    level_str = os.getenv("LOG_LEVEL", "INFO")
    return getattr(logging, level_str.upper(), logging.INFO)

if __name__ == "__main__":
    config = load_config()
    print(f"Config: {config}")
    print(f"Model Path: {get_model_path()}")
    print(f"Dataset ID: {get_dataset_id()}")

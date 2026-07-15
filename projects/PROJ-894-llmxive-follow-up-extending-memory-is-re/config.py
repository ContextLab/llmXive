"""
Configuration module for the llmXive project.

Provides centralized configuration for model paths, cache directories, and other settings.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any

# Project root directory
PROJECT_ROOT = Path(__file__).parent

# Default model configuration
DEFAULT_MODEL_ID = "TheBloke/Llama-2-7B-Chat-GGUF"
DEFAULT_MODEL_FILENAME = "llama-2-7b-chat.Q4_K_M.gguf"

# Cache directory for downloaded models
DEFAULT_CACHE_DIR = PROJECT_ROOT / "data" / "models"

def get_model_path() -> Optional[str]:
    """
    Get the configured model path from environment variable or config file.
    
    Returns:
        Optional[str]: Path to the model file, or None if not configured.
    """
    # Check environment variable first
    env_path = os.getenv("LLMXIVE_MODEL_PATH")
    if env_path and os.path.exists(env_path):
        return env_path
    
    # Check for config file
    config_file = PROJECT_ROOT / "config.yaml"
    if config_file.exists():
        import yaml
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
            model_path = config.get('model_path')
            if model_path and os.path.exists(model_path):
                return model_path
    
    return None

def get_huggingface_cache_dir() -> str:
    """
    Get the cache directory for HuggingFace downloads.
    
    Returns:
        str: Path to the cache directory.
    """
    # Check environment variable
    env_cache = os.getenv("HF_HOME")
    if env_cache:
        return env_cache
    
    # Default to project data/models directory
    return str(DEFAULT_CACHE_DIR)

def get_config() -> Dict[str, Any]:
    """
    Load all configuration from config.yaml if it exists.
    
    Returns:
        Dict[str, Any]: Configuration dictionary.
    """
    config_file = PROJECT_ROOT / "config.yaml"
    default_config = {
        'model_path': None,
        'huggingface_cache_dir': str(DEFAULT_CACHE_DIR),
        'inference': {
            'max_tokens': 512,
            'temperature': 0.7,
            'n_ctx': 4096,
            'n_threads': 4
        }
    }
    
    if config_file.exists():
        import yaml
        with open(config_file, 'r') as f:
            user_config = yaml.safe_load(f)
            # Merge with defaults
            for key in user_config:
                if isinstance(user_config[key], dict) and key in default_config and isinstance(default_config[key], dict):
                    default_config[key].update(user_config[key])
                else:
                    default_config[key] = user_config[key]
    
    return default_config
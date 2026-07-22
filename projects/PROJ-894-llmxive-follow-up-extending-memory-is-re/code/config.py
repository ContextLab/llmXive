"""
Configuration module for project settings.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any

# Default model configuration
DEFAULT_MODEL_REPO = "TheBloke/Llama-2-7B-Chat-GGUF"
DEFAULT_MODEL_FILENAME = "llama-2-7b-chat.Q4_K_M.gguf"
DEFAULT_CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "llmxive")

def get_model_path() -> str:
    """
    Get the path to the LLM model.
    
    Returns:
        Path to the model file. If not found, returns the default download path.
    """
    # Check for environment variable
    model_path = os.getenv("LLMXIVE_MODEL_PATH")
    if model_path and os.path.exists(model_path):
        return model_path
    
    # Check in default cache directory
    cache_dir = get_huggingface_cache_dir()
    default_path = os.path.join(cache_dir, "models", DEFAULT_MODEL_FILENAME)
    
    if os.path.exists(default_path):
        return default_path
    
    # Return the path where the model should be downloaded
    return default_path

def get_huggingface_cache_dir() -> str:
    """
    Get the HuggingFace cache directory.
    
    Returns:
        Path to the cache directory.
    """
    # Check for environment variable
    cache_dir = os.getenv("HF_HOME")
    if cache_dir:
        return cache_dir
    
    # Use default cache directory
    return os.path.join(os.path.expanduser("~"), ".cache", "huggingface")

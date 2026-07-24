"""
Configuration loader for the pipeline.
Reads from code/config.yaml.
"""
import yaml
from pathlib import Path
from typing import Dict, Any

def load_config() -> Dict[str, Any]:
    """
    Loads the configuration from code/config.yaml.
    
    Returns:
        dict: Configuration dictionary containing prompts, seeds, and paths.
    """
    config_path = Path(__file__).parent / "config.yaml"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    return config

# For backward compatibility if imported as `from config import load_config`
# The main.py likely uses `from config import load_config` or similar
# We ensure the function is available.

# Default config content if file is missing (for T004 generation if needed)
DEFAULT_CONFIG = {
    "prompts": [
        "a futuristic city with neon lights",
        "a serene landscape with mountains and lakes",
        "a portrait of a person with cybernetic implants"
    ],
    "seeds": [42, 123, 456],
    "base_model": "runwayml/stable-diffusion-v1-5",
    "adapter_path": "data/models/adapter_fp16.safetensors"
}

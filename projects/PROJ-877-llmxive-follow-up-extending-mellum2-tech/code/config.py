"""
Configuration management module for the llmXive pipeline.
Handles environment variables, project root detection, and seed setting.
"""
import os
import random
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_project_root() -> Path:
    """
    Get the project root directory.
    
    Returns:
        Path object pointing to the project root.
    """
    # Check for explicit environment variable first
    root_env = os.getenv("PROJECT_ROOT")
    if root_env:
        return Path(root_env).resolve()
        
    # Otherwise, assume current working directory or parent of this file
    # In the context of this project, we assume the script runs from the project root
    current_file = Path(__file__).resolve()
    # Navigate up to find the project root (assuming code/ subdirectory exists)
    if current_file.name == "config.py" and current_file.parent.name == "code":
        return current_file.parent.parent
    return Path.cwd()

def load_environment() -> Dict[str, str]:
    """
    Load all environment variables into a dictionary.
    
    Returns:
        Dictionary of environment variables.
    """
    return dict(os.environ)

def validate_required_env_vars(required_vars: List[str]) -> bool:
    """
    Validate that all required environment variables are set.
    
    Args:
        required_vars: List of required environment variable names.
        
    Returns:
        True if all variables are set, False otherwise.
    """
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        raise ValueError(f"Missing required environment variables: {missing}")
    return True

def get_config() -> Dict[str, Any]:
    """
    Get the configuration dictionary from environment variables.
    
    Returns:
        Configuration dictionary.
    """
    config = {
        "project_root": str(get_project_root()),
        "hf_token": os.getenv("HF_TOKEN", ""),
        "hf_dataset_name": os.getenv("HF_DATASET_NAME", "codeparrot/github-code"),
        "max_workers": int(os.getenv("MAX_WORKERS", "4")),
        "timeout_seconds": int(os.getenv("TIMEOUT_SECONDS", "300")),
        "seed": int(os.getenv("RANDOM_SEED", "42")),
        "batch_size": int(os.getenv("BATCH_SIZE", "1")),
        "device": os.getenv("DEVICE", "cpu"),
    }
    return config

def set_seed(seed: Optional[int] = None) -> None:
    """
    Set random seeds for reproducibility.
    
    Args:
        seed: Random seed value. If None, uses default from config.
    """
    if seed is None:
        seed = get_config().get("seed", 42)
        
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    
    # Try to set numpy and torch seeds if available
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass
        
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass

def ensure_dirs(base_path: Path, dirs: List[str]) -> List[Path]:
    """
    Ensure a list of directories exist under a base path.
    
    Args:
        base_path: Base directory path.
        dirs: List of directory names to create.
        
    Returns:
        List of created directory paths.
    """
    created = []
    for d in dirs:
        path = base_path / d
        path.mkdir(parents=True, exist_ok=True)
        created.append(path)
    return created

def main() -> int:
    """
    Main entry point for config validation.
    
    Returns:
        0 on success, 1 on failure.
    """
    try:
        config = get_config()
        print(f"Configuration loaded successfully:")
        for key, value in config.items():
            # Mask sensitive values
            if "token" in key.lower() or "secret" in key.lower():
                value = "***"
            print(f"  {key}: {value}")
        return 0
    except Exception as e:
        print(f"Configuration error: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())

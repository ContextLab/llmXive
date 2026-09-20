"""
Setup script to create the model cache directory.

This task (T005) creates the `models/` directory at the project root
to serve as the cache for downloaded model weights (e.g., Kwai Keye-VL).
"""
import os
from pathlib import Path


def ensure_model_cache_directory() -> Path:
    """
    Ensure the model cache directory exists.
    
    Returns:
        Path: The absolute path to the models directory.
        
    Raises:
        OSError: If the directory cannot be created.
    """
    # Define the path relative to the script's location (project root)
    # The script is located at code/setup_model_cache.py, so project root is parent of code/
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    models_dir = project_root / "models"
    
    if not models_dir.exists():
        models_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created model cache directory: {models_dir}")
    else:
        print(f"Model cache directory already exists: {models_dir}")
        
    return models_dir


def main():
    """Main entry point for the setup script."""
    try:
        models_dir = ensure_model_cache_directory()
        print(f"Success: Model cache ready at {models_dir}")
    except OSError as e:
        print(f"Error: Failed to create model cache directory: {e}")
        raise


if __name__ == "__main__":
    main()
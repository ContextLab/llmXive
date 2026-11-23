import os
from pathlib import Path

def ensure_model_cache_directory():
    """
    Creates the 'models/' directory at the project root if it does not already exist.
    This directory serves as the cache for downloaded model weights and checkpoints.
    """
    project_root = Path(__file__).resolve().parent.parent
    models_dir = project_root / "models"
    
    if not models_dir.exists():
        models_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created model cache directory: {models_dir}")
    else:
        print(f"Model cache directory already exists: {models_dir}")
    
    return models_dir

def main():
    """Entry point for script execution."""
    ensure_model_cache_directory()

if __name__ == "__main__":
    main()
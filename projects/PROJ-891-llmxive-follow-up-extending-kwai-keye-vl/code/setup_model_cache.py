import os
from pathlib import Path

def ensure_model_cache_directory(base_path: str = "models") -> Path:
    """
    Creates the model cache directory if it does not exist.
    
    Args:
        base_path: The relative path to the model cache directory (default: 'models').
        
    Returns:
        Path: The absolute path to the created or existing directory.
    """
    cache_dir = Path(base_path)
    
    # Ensure the directory exists
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Verify permissions (optional but good practice for cache dirs)
    if not os.access(cache_dir, os.W_OK):
        raise PermissionError(f"Write permission denied for model cache directory: {cache_dir}")
        
    return cache_dir

def main():
    """
    Entry point for setting up the model cache directory.
    Creates the 'models' directory at the project root.
    """
    try:
        model_dir = ensure_model_cache_directory()
        print(f"Model cache directory ready: {model_dir}")
    except Exception as e:
        print(f"Error setting up model cache directory: {e}")
        raise

if __name__ == "__main__":
    main()
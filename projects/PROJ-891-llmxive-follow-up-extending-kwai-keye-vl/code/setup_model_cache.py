"""
Setup script to create the model cache directory.
This directory is used to store downloaded model weights and caches for inference.
"""
import os
from pathlib import Path


def ensure_model_cache_directory(base_path: Path | None = None) -> Path:
    """
    Ensures the model cache directory exists.
    
    Args:
        base_path: The root directory of the project. Defaults to the current working directory.
        
    Returns:
        The Path object for the created/existing model cache directory.
        
    Raises:
        OSError: If the directory cannot be created.
    """
    if base_path is None:
        base_path = Path.cwd()
        
    cache_dir = base_path / "models"
    
    if not cache_dir.exists():
        try:
            cache_dir.mkdir(parents=True, exist_ok=True)
            # Create a .gitkeep file to ensure the directory is tracked by git
            # even if it's empty initially.
            keep_file = cache_dir / ".gitkeep"
            keep_file.touch()
        except OSError as e:
            raise OSError(f"Failed to create model cache directory at {cache_dir}: {e}")
    
    return cache_dir


def main() -> None:
    """Main entry point for the script."""
    print("Setting up model cache directory...")
    try:
        cache_dir = ensure_model_cache_directory()
        print(f"Model cache directory ready at: {cache_dir}")
    except OSError as e:
        print(f"Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()

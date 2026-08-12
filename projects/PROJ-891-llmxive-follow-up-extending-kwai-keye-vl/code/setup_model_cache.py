"""
Setup script to create the model cache directory structure.

This task (T005) initializes the `models/` directory at the project root
to store downloaded model weights and caches for the Kwai Keye-VL and
other inference dependencies.
"""
import os
from pathlib import Path


def ensure_model_cache_directory(root_dir: Path) -> Path:
    """
    Create the model cache directory if it does not exist.
    
    Args:
        root_dir: The project root directory.
        
    Returns:
        The path to the created or existing model cache directory.
        
    Raises:
        OSError: If the directory cannot be created due to permissions or other OS errors.
    """
    models_dir = root_dir / "models"
    if not models_dir.exists():
        models_dir.mkdir(parents=True, exist_ok=True)
        # Optional: Set specific permissions if needed, though default is usually fine
        # os.chmod(models_dir, 0o755) 
    return models_dir


def main() -> None:
    """
    Entry point for the model cache setup script.
    
    Creates the 'models' directory relative to the current working directory
    (assumed to be the project root).
    """
    root = Path.cwd()
    models_path = ensure_model_cache_directory(root)
    print(f"Model cache directory ready: {models_path}")


if __name__ == "__main__":
    main()
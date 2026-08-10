import os
from pathlib import Path
from typing import List
from utils.logging import get_logger, info, warning, error

logger = get_logger(__name__)

def create_data_directories(base_path: Optional[Path] = None) -> List[Path]:
    """
    Creates the required directory structure for the project data:
    - data/raw/
    - data/processed/
    - data/results/

    Args:
        base_path: Optional base path. Defaults to project root (parent of code/).

    Returns:
        List of created Path objects.
    """
    if base_path is None:
        # Infer project root as the parent of the code directory
        current_file = Path(__file__).resolve()
        base_path = current_file.parent.parent

    data_root = base_path / "data"
    directories = [
        data_root / "raw",
        data_root / "processed",
        data_root / "results"
    ]

    created_paths = []
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
            created_paths.append(dir_path)
        else:
            logger.debug(f"Directory already exists: {dir_path}")
            created_paths.append(dir_path)

    return created_paths

def main():
    """Entry point for directory creation script."""
    logger.info("Starting data directory setup...")
    try:
        dirs = create_data_directories()
        logger.info(f"Successfully ensured {len(dirs)} data directories.")
        for d in dirs:
            info(f"  - {d}")
    except Exception as e:
        error(f"Failed to create data directories: {e}")
        raise

if __name__ == "__main__":
    main()
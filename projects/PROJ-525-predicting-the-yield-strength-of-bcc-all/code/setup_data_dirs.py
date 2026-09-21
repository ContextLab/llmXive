"""
Setup script for data directory structure.
Creates data/raw, data/processed, and data/logs directories with .gitkeep files.
Generates checksums for the created structure.
"""
import os
import sys
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import ensure_dirs, save_checksums, compute_directory_checksum
from utils import setup_logger

logger = setup_logger(__name__)

def create_gitkeep(directory: Path) -> None:
    """Create a .gitkeep file in the specified directory."""
    gitkeep_path = directory / ".gitkeep"
    if not gitkeep_path.exists():
        gitkeep_path.touch()
        logger.info(f"Created .gitkeep in {directory}")
    else:
        logger.debug(f".gitkeep already exists in {directory}")

def setup_data_directories() -> None:
    """Create the required data directory structure."""
    data_dirs = [
        "data/raw",
        "data/processed",
        "data/logs"
    ]

    for dir_path_str in data_dirs:
        dir_path = project_root / dir_path_str
        ensure_dirs([dir_path])
        create_gitkeep(dir_path)
        logger.info(f"Ensured directory: {dir_path}")

def generate_checksums() -> None:
    """Generate checksums for the data directories."""
    data_root = project_root / "data"
    if data_root.exists():
        checksums = []
        for item in data_root.iterdir():
            if item.is_dir():
                checksum = compute_directory_checksum(item)
                checksums.append({
                    "path": str(item.relative_to(project_root)),
                    "checksum": checksum,
                    "type": "directory"
                })
                logger.info(f"Computed checksum for {item}: {checksum}")

        if checksums:
            save_checksums(checksums, project_root / "data" / "checksums.json")
            logger.info("Saved checksums to data/checksums.json")

def main() -> int:
    """Main entry point for the setup script."""
    logger.info("Starting data directory setup...")
    
    try:
        setup_data_directories()
        generate_checksums()
        logger.info("Data directory setup completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Error during setup: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

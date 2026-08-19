import os
import sys
import logging
from pathlib import Path

# Add parent directory to path to allow imports from code/
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.checksum_utils import initialize_data_structure, generate_checksum_manifest
from config import ensure_directories

logger = logging.getLogger(__name__)

def main():
    """
    Main entry point to initialize the data directory structure and generate an initial checksum manifest.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Ensure the data directory exists
    data_root = project_root / "data"
    
    logger.info(f"Initializing data directory structure at {data_root}...")
    
    # Initialize the subdirectories (raw, processed, validation)
    initialize_data_structure(data_root)
    
    # Ensure config directories are also ready (if needed)
    ensure_directories()
    
    # Generate an initial empty manifest or verify structure
    # Since no files exist yet, we just verify the directories exist
    sub_dirs = ["raw", "processed", "validation"]
    for subdir in sub_dirs:
        dir_path = data_root / subdir
        if not dir_path.exists():
            logger.error(f"Failed to create directory: {dir_path}")
            sys.exit(1)
        logger.info(f"Verified directory: {dir_path}")
    
    # Create an initial manifest indicating the structure is ready
    # We generate a manifest for the .gitkeep files or just an empty structure entry
    manifest_path = data_root / "manifest.json"
    # Generate manifest for the directories themselves (as a placeholder)
    # or just create an empty one if no files yet.
    # For now, we generate a manifest with the .gitkeep files if they exist
    files_to_check = []
    for subdir in sub_dirs:
        gitkeep = data_root / subdir / ".gitkeep"
        if gitkeep.exists():
            rel_path = f"{subdir}/.gitkeep"
            files_to_check.append(rel_path)
    
    if files_to_check:
        generate_checksum_manifest(data_root, files_to_check, manifest_path)
        logger.info(f"Initial checksum manifest created at {manifest_path}")
    else:
        # If no files, create an empty manifest structure
        import json
        manifest = {
            "base_dir": str(data_root),
            "files": {}
        }
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"Empty checksum manifest created at {manifest_path} (no files yet).")

    logger.info("Data directory initialization complete.")

if __name__ == "__main__":
    main()

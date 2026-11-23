import os
import sys
import logging
from pathlib import Path

# Add code directory to path
code_root = Path(__file__).parent
sys.path.insert(0, str(code_root))

from src.utils.io_utils import ensure_dirs, validate_project_structure, get_data_stats, update_checksums
from src.utils.logging import setup_default_loggers

logger = logging.getLogger(__name__)

def main():
    """
    Task T005: Setup data directory structure and checksumming utilities.
    Creates: data/raw, data/curated, data/eval, data/validation
    """
    # Setup logging
    setup_default_loggers()
    
    # Determine project root based on this script location
    # Assuming script is in code/ and we want to write to projects/.../code/
    # But T001/T001b/T001c created the structure. We just need to ensure data dirs exist
    # and initialize the checksum file.
    
    # The prompt says "Setup data directory structure... with checksumming utilities in src/utils/io_utils.py"
    # The utilities are implemented in io_utils.py (artifact 1).
    # This script ensures the directories exist and initializes the checksum manifest.
    
    # Assuming the project root is the parent of the code directory
    project_root = code_root.parent 
    # If running from code/ directly, parent is the project root for T001 structure
    # T001 created projects/PROJ-.../code/
    # So code_root is projects/PROJ-.../code/
    
    data_base = project_root / "data"
    
    required_data_dirs = [
        "raw",
        "curated",
        "eval",
        "validation"
    ]
    
    full_paths = [data_base / d for d in required_data_dirs]
    
    logger.info(f"Ensuring data directories exist in {data_base}")
    ensure_dirs(full_paths)
    
    # Initialize checksum manifest
    checksum_manifest = data_base / "checksums.json"
    if not checksum_manifest.exists():
        # Create initial empty manifest or scan if files exist
        logger.info(f"Initializing checksum manifest at {checksum_manifest}")
        # Calculate initial checksums (likely empty)
        update_checksums(data_base, checksum_manifest)
    
    # Validate structure
    is_valid, missing = validate_project_structure(data_base, required_data_dirs)
    if is_valid:
        logger.info("Data directory structure validated successfully.")
    else:
        logger.error(f"Data directory structure validation failed. Missing: {missing}")
        sys.exit(1)
        
    # Log stats
    stats = get_data_stats(data_base, required_data_dirs)
    logger.info(f"Data stats: {stats}")
    
    print(f"T005 Complete: Data structure created at {data_base}")
    print(f"Checksums initialized at {checksum_manifest}")

if __name__ == "__main__":
    main()
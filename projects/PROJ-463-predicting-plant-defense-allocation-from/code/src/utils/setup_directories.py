import os
import sys
from pathlib import Path
from .config import get_data_path, get_config
from .logger import get_logger

def setup_data_directories():
    """
    Creates the required directory structure for the plant defense allocation project.
    
    Creates the following directories under the data root (as defined in config):
    - data/raw: For unaltered files fetched from NCBI GEO/SRA
    - data/processed: For processed TPM matrices and QC outputs
    - data/traits: For defense trait data from TRY/Phenoscape
    - data/manifests: For JSON manifests tracking files and checksums
    - data/synthetic: For synthetic TPM count matrices (prototype validation only)
    
    Returns:
        dict: A dictionary mapping directory names to their absolute Path objects
    """
    logger = get_logger(__name__)
    logger.info("Setting up data directory structure...")
    
    # Get the base data path from configuration
    data_root = get_data_path()
    if not data_root:
        # Fallback to default if config not set
        data_root = Path("data")
        logger.warning(f"Data path not in config, using default: {data_root}")
    
    # Ensure base data directory exists
    data_root.mkdir(parents=True, exist_ok=True)
    logger.info(f"Base data directory: {data_root}")
    
    # Define required subdirectories
    required_dirs = [
        "raw",
        "processed",
        "traits",
        "manifests",
        "synthetic"
    ]
    
    created_paths = {}
    
    for dir_name in required_dirs:
        dir_path = data_root / dir_name
        
        # Create directory if it doesn't exist
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
        else:
            logger.info(f"Directory already exists: {dir_path}")
        
        created_paths[dir_name] = dir_path
    
    # Create .gitkeep files to ensure directories are tracked by git
    for dir_name, dir_path in created_paths.items():
        gitkeep_path = dir_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            logger.debug(f"Created .gitkeep in {dir_path}")
    
    logger.info("Directory structure setup complete.")
    return created_paths

def main():
    """Entry point for running directory setup as a script."""
    logger = get_logger(__name__)
    try:
        paths = setup_data_directories()
        logger.info("Successfully created directory structure:")
        for name, path in paths.items():
            logger.info(f"  - {name}: {path}")
        return 0
    except Exception as e:
        logger.error(f"Failed to setup directory structure: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())

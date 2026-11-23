import os
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_data_directories(base_path: Path) -> None:
    """
    Create the required data directory structure for the project.
    
    Creates:
    - data/processed: For intermediate and final processed data
    - data/checksums: For storing checksums of data artifacts
    - data/raw: For raw downloaded data
    
    Args:
        base_path: The root path of the project
    """
    data_dir = base_path / "data"
    processed_dir = data_dir / "processed"
    checksums_dir = data_dir / "checksums"
    raw_dir = data_dir / "raw"
    
    directories = [processed_dir, checksums_dir, raw_dir]
    
    for directory in directories:
        if not directory.exists():
            logger.info(f"Creating directory: {directory}")
            directory.mkdir(parents=True, exist_ok=True)
        else:
            logger.info(f"Directory already exists: {directory}")

def main() -> int:
    """
    Main entry point for the data directory setup script.
    
    Returns:
        int: 0 on success, 1 on failure
    """
    try:
        # Determine the project root (assumed to be two levels up from this script)
        script_path = Path(__file__).resolve()
        project_root = script_path.parent.parent
        
        logger.info(f"Project root: {project_root}")
        
        create_data_directories(project_root)
        
        # Verification
        data_dir = project_root / "data"
        processed_dir = data_dir / "processed"
        checksums_dir = data_dir / "checksums"
        raw_dir = data_dir / "raw"
        
        if processed_dir.exists() and checksums_dir.exists() and raw_dir.exists():
            logger.info("All data directories created and verified successfully.")
            print("OK")
            return 0
        else:
            logger.error("Directory creation verification failed.")
            return 1
            
    except Exception as e:
        logger.error(f"Error during directory creation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
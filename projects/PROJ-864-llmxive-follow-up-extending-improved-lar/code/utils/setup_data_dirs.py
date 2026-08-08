"""
Setup data directory structure for the project.
"""
import os
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.logging import get_logger, info, error

logger = get_logger(__name__)

def setup_data_directories():
    """
    Create the required directory structure for data.
    
    Creates:
    - data/raw/
    - data/processed/
    - data/artifacts/
    
    Returns:
        Path to the data directory
    """
    try:
        data_root = project_root / "data"
        raw_dir = data_root / "raw"
        processed_dir = data_root / "processed"
        artifacts_dir = data_root / "artifacts"
        
        # Create directories
        data_root.mkdir(parents=True, exist_ok=True)
        raw_dir.mkdir(parents=True, exist_ok=True)
        processed_dir.mkdir(parents=True, exist_ok=True)
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for raw data sources
        gutenberg_dir = raw_dir / "gutenberg"
        stack_dir = raw_dir / "stack"
        gutenberg_dir.mkdir(parents=True, exist_ok=True)
        stack_dir.mkdir(parents=True, exist_ok=True)
        
        info(f"Data directories created at {data_root}")
        return data_root
        
    except Exception as e:
        error(f"Failed to create data directories: {e}")
        raise

if __name__ == "__main__":
    setup_data_directories()

import os
from pathlib import Path
from code.utils.logger import get_logger

logger = get_logger(__name__)

PROJECT_ROOT = "projects/PROJ-446-predicting-molecular-halide-binding-affi"

def main():
    """Create the project root directory if it does not exist."""
    root_path = Path(PROJECT_ROOT)
    
    if root_path.exists():
        logger.info(f"Directory {PROJECT_ROOT} already exists.")
        return
    
    root_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Successfully created project root directory: {PROJECT_ROOT}")
    
    # Create a marker file to confirm existence
    marker = root_path / ".project_marker"
    marker.write_text(f"Project: {PROJECT_ROOT}\nCreated: {root_path.stat().st_mtime}\n")
    logger.info(f"Created marker file: {marker}")

if __name__ == "__main__":
    main()
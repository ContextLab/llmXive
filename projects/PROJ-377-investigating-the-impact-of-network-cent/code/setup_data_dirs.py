import os
from pathlib import Path

def setup_data_directories():
    """
    Create the project data directory structure as specified in T005b.
    
    Creates:
    - data/
    - data/raw/
    - data/processed/
    - data/artifacts/
    
    Ensures all directories exist, creating them if necessary.
    """
    base_dir = Path("data")
    subdirs = ["raw", "processed", "artifacts"]
    
    created_dirs = []
    
    # Ensure base directory exists
    base_dir.mkdir(parents=True, exist_ok=True)
    created_dirs.append(str(base_dir))
    
    # Create subdirectories
    for subdir in subdirs:
        dir_path = base_dir / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        created_dirs.append(str(dir_path))
    
    # Create additional required subdirectories for processed data
    # as referenced in tasks.md (e.g., behavioral, centrality, logs, etc.)
    processed_base = base_dir / "processed"
    additional_subdirs = [
        "behavioral",
        "centrality",
        "fmriprep",
        "regression",
        "validation",
        "logs"
    ]
    
    for subdir in additional_subdirs:
        dir_path = processed_base / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        created_dirs.append(str(dir_path))
    
    return created_dirs

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("Setting up data directory structure...")
    dirs = setup_data_directories()
    logger.info(f"Created directories: {dirs}")
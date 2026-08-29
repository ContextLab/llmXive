import os
from pathlib import Path

def create_project_directories():
    """
    Create the required directory structure for the project.
    
    Creates the following directories relative to the project root:
    - data/raw
    - data/processed
    - results
    - tests/unit
    - tests/contract
    
    This function is idempotent; it will not fail if directories already exist.
    """
    project_root = Path(__file__).resolve().parent.parent
    
    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "results",
        project_root / "tests" / "unit",
        project_root / "tests" / "contract",
    ]
    
    created_count = 0
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
        else:
            # Ensure it is actually a directory
            if not dir_path.is_dir():
                raise RuntimeError(f"Path exists but is not a directory: {dir_path}")
    
    return created_count

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    count = create_project_directories()
    logger.info(f"Successfully created or verified {count} directory structure(s).")
    logger.info("Directory structure ready for data pipeline and analysis.")
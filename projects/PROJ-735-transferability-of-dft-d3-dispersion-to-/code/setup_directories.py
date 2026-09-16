import os
from pathlib import Path
from logger import get_logger, info, error

logger = get_logger(__name__)

def main():
    """
    Create the required directory structure for the project.
    This is a foundational task to ensure data/raw, data/derived, docs, and figures exist.
    """
    project_root = Path(__file__).parent.parent
    
    required_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "derived",
        project_root / "figures",
        project_root / "docs",
        project_root / "code",
        project_root / "tests",
    ]
    
    created_count = 0
    for dir_path in required_dirs:
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            info(f"Directory ensured: {dir_path}")
            created_count += 1
        except Exception as e:
            error(f"Failed to create directory {dir_path}: {e}")
    
    if created_count == len(required_dirs):
        info(f"Successfully ensured {created_count} directories.")
    else:
        error(f"Only {created_count}/{len(required_dirs)} directories created successfully.")

if __name__ == "__main__":
    main()
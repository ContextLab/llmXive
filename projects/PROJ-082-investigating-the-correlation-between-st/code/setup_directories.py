import os
import sys
from pathlib import Path

def main():
    """Initialize project directory structure."""
    # Determine project root (assuming this script is in code/)
    project_root = Path(__file__).resolve().parent.parent
    
    dirs = ["code", "tests", "data", "docs", "figures", "contracts"]
    
    for dir_name in dirs:
        dir_path = project_root / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created/Verified: {dir_path}")
    
    # Create subdirectories for data
    data_subdirs = ["raw", "derived", "interim"]
    for subdir in data_subdirs:
        (project_root / "data" / subdir).mkdir(parents=True, exist_ok=True)
        print(f"Created/Verified: {project_root / 'data' / subdir}")

if __name__ == "__main__":
    main()

import os
import sys
from pathlib import Path

def main():
    """Create project directory structure as defined in T001a."""
    project_root = Path(__file__).resolve().parent.parent
    
    # Define all required directories relative to project root
    dirs = [
        "code",
        "code/utils",
        "tests",
        "data/raw",
        "data/processed",
        "data/synthetic",
        "models",
        "docs",
        "docs/contracts",
        "state/projects",
        "logs"  # Added for logging infrastructure (T008)
    ]
    
    created_count = 0
    for dir_name in dirs:
        full_path = project_root / dir_name
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path.relative_to(project_root)}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path.relative_to(project_root)}")
    
    print(f"Project structure initialized. Created {created_count} new directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())

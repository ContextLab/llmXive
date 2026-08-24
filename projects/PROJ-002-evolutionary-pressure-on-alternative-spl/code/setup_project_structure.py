import os
from pathlib import Path

def create_directories():
    """
    Creates the required project directory structure for PROJ-002.
    Directories created:
      - src/ (source code)
      - tests/ (test suites)
      - config/ (configuration files)
      - data/ (raw and processed data)
      - results/ (final outputs and figures)
      - docs/ (documentation)
    """
    project_root = Path(__file__).parent.parent
    
    required_dirs = [
        "src",
        "tests",
        "config",
        "data",
        "results",
        "docs"
    ]
    
    created_count = 0
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
        # Ensure tests subdirectories exist as per T001c requirement
        if dir_name == "tests":
            subdirs = ["unit", "integration", "contract"]
            for subdir in subdirs:
                subdir_path = dir_path / subdir
                if not subdir_path.exists():
                    subdir_path.mkdir(parents=True, exist_ok=True)
                    created_count += 1
    
    print(f"Project structure created: {created_count} directories.")
    return True

if __name__ == "__main__":
    success = create_directories()
    if success:
        print("Directory structure initialization complete.")
    else:
        print("Failed to initialize directory structure.")
        exit(1)
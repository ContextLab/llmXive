import os
from pathlib import Path
from setup_directories import create_directories

def main() -> None:
    """
    Entry point for creating the full project directory structure.
    Calls setup_directories to create root and subdirectories (T001a & T001b).
    """
    project_root = Path.cwd()
    
    # Root directories (T001a)
    root_dirs = [
        "projects/PROJ-526-quantifying-the-impact-of-dataset-size-o",
        "code",
        "data",
        "tests",
        "state",
        "docs"
    ]
    
    # Subdirectories (T001b)
    sub_dirs = [
        "data/raw",
        "data/processed",
        "tests/contract",
        "tests/unit",
        "tests/integration"
    ]
    
    print(f"Creating full directory structure in: {project_root}")
    create_directories(project_root, root_dirs)
    create_directories(project_root, sub_dirs)
    
    # Verify creation
    all_dirs = root_dirs + sub_dirs
    for d in all_dirs:
        if (project_root / d).exists():
            print(f"  [OK] {d}")
        else:
            print(f"  [FAIL] {d}")
            raise RuntimeError(f"Failed to create directory: {d}")

    print("Full directory structure created successfully.")

if __name__ == "__main__":
    main()

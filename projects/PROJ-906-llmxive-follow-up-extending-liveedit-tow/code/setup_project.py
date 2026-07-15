import os
import sys
from pathlib import Path

def main():
    """
    Creates the project directory structure for PROJ-906-llmxive-follow-up-extending-liveedit-tow.
    Ensures all required subdirectories exist under the project root.
    """
    project_root = Path("projects/PROJ-906-llmxive-follow-up-extending-liveedit-tow")
    
    # Define the required directory structure relative to the project root
    required_dirs = [
        "data/raw",
        "data/flow",
        "data/metrics",
        "code",
        "code/data",
        "code/models",
        "code/metrics",
        "code/analysis",
        "tests/contract",
        "tests/unit",
        "results"
    ]

    print(f"Creating project structure at: {project_root.absolute()}")

    created_count = 0
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"  Created: {full_path.relative_to(project_root)}")
            created_count += 1
        else:
            # Ensure it is a directory, not a file
            if not full_path.is_dir():
                print(f"  ERROR: Path exists but is not a directory: {full_path}")
                sys.exit(1)
            # print(f"  Exists: {full_path.relative_to(project_root)}")

    # Create __init__.py files to make code directories importable
    # This is a common convention for Python projects, though not explicitly requested,
    # it ensures 'code' acts as a package if imported from root.
    # We will create __init__.py in the immediate code subfolders to be safe.
    init_folders = [
        "code",
        "code/data",
        "code/models",
        "code/metrics",
        "code/analysis",
        "tests/contract",
        "tests/unit"
    ]
    
    for folder in init_folders:
        init_file = project_root / folder / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            # print(f"  Created init: {init_file.relative_to(project_root)}")

    print(f"\nProject structure initialization complete. {created_count} new directories created.")
    print(f"Project Root: {project_root}")
    print("\nDirectory Tree:")
    print_tree(project_root)

def print_tree(start_path):
    """Prints a simple tree structure of the directories."""
    start_path = Path(start_path)
    if not start_path.exists():
        return

    # List directories only for the tree
    items = sorted(start_path.iterdir())
    dirs = [item for item in items if item.is_dir()]
    
    for i, item in enumerate(dirs):
        is_last = i == len(dirs) - 1
        prefix = "└── " if is_last else "├── "
        print(f"{prefix}{item.name}")
        
        # Recursively print subdirectories (limit depth to avoid noise)
        if item.name in ["data", "code", "tests"]:
            sub_items = sorted(item.iterdir())
            sub_dirs = [sub for sub in sub_items if sub.is_dir()]
            for j, sub_dir in enumerate(sub_dirs):
                sub_is_last = j == len(sub_dirs) - 1
                sub_prefix = "    " if is_last else "│   "
                sub_prefix += "└── " if sub_is_last else "├── "
                print(f"{sub_prefix}{sub_dir.name}")

if __name__ == "__main__":
    main()

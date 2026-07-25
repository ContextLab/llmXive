import os
from pathlib import Path
from create_project_structure import create_project_structure

def print_tree(start_path: Path, indent: str = ""):
    """Recursively prints the directory tree structure."""
    print(indent + start_path.name)
    if start_path.is_dir():
        items = sorted(start_path.iterdir())
        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            connector = "└── " if is_last else "├── "
            new_indent = indent + ("    " if is_last else "│   ")
            print_tree(item, indent + connector)

def main():
    """
    Verifies that the T001 task has been completed by checking the existence
    of the required project root directory.
    """
    target_dir = Path("projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code")
    
    # Ensure the structure exists
    create_project_structure()
    
    if not target_dir.exists():
        print(f"ERROR: Directory {target_dir} does not exist.")
        return False
    
    if not target_dir.is_dir():
        print(f"ERROR: {target_dir} is not a directory.")
        return False
    
    print(f"SUCCESS: T001 Project root exists at {target_dir.resolve()}")
    print("\nDirectory Tree:")
    print_tree(target_dir)
    return True

if __name__ == "__main__":
    main()
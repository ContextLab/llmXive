import os
from pathlib import Path
from create_project_structure import create_project_structure

def print_tree(path, prefix=""):
    """Recursively prints the directory tree."""
    path = Path(path)
    if not path.exists():
        print(f"{prefix}[MISSING] {path.name}")
        return

    print(f"{prefix}[DIR ] {path.name}")
    
    try:
        items = sorted(path.iterdir())
    except PermissionError:
        print(f"{prefix}  [ERR  ] Permission denied")
        return

    for i, item in enumerate(items):
        is_last = i == len(items) - 1
        extension = "└── " if is_last else "├── "
        child_prefix = prefix + ("    " if is_last else "│   ")
        
        if item.is_dir():
            print(f"{prefix}{extension}{item.name}/")
            print_tree(item, child_prefix)
        else:
            print(f"{prefix}{extension}{item.name}")

def main():
    target_path = Path("projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code")
    
    print(f"Verifying structure at: {target_path}")
    if not target_path.exists():
        print("ERROR: Target directory does not exist. Please run T001 first.")
        return False
    
    print_tree(target_path)
    return True

if __name__ == "__main__":
    main()

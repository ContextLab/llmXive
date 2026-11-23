import os
import sys
from pathlib import Path

def create_directories():
    """Create the contracts directory structure as defined in T001e."""
    root = Path(__file__).resolve().parent.parent
    contracts_root = root / "contracts"
    
    subdirs = [
        contracts_root / "scene",
        contracts_root / "trajectory",
        contracts_root / "stats"
    ]
    
    for subdir in subdirs:
        subdir.mkdir(parents=True, exist_ok=True)
        # Create a placeholder README to ensure the directory is tracked
        readme = subdir / "README.md"
        if not readme.exists():
            readme.write_text(f"# {subdir.name} Contracts\n\nThis directory contains contract definitions for {subdir.name}.\n")
    
    return contracts_root

def print_tree(root_path: Path):
    """Print the directory tree for the contracts folder."""
    print(f"Contracts structure created at: {root_path}")
    for root, dirs, files in os.walk(root_path):
        level = root.relative_to(root_path).parts
        indent = "  " * len(level)
        print(f"{indent}{Path(root).name}/")
        sub_indent = "  " * (len(level) + 1)
        for file in files:
            print(f"{sub_indent}{file}")

def main():
    root = create_directories()
    print_tree(root)

if __name__ == "__main__":
    main()

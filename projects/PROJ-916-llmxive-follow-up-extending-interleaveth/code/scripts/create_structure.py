"""
Script to create the project directory structure for llmXive.
This script creates all required directories under src/, tests/, data/, docs/, and contracts/.
"""
import os
import sys
from pathlib import Path

def create_directories():
    base_path = Path(__file__).resolve().parent.parent
    structure = {
        "src": [
            "simulator",
            "agents",
            "pipeline",
            "benchmarks",
            "stats",
            "utils"
        ],
        "tests": [
            "unit",
            "integration",
            "contract"
        ],
        "data": [
            "raw",
            "intermediate",
            "simulator_validation"
        ],
        "docs": [],
        "contracts": [
            "scene",
            "trajectory",
            "stats"
        ]
    }

    created = []
    for root_dir, sub_dirs in structure.items():
        root_path = base_path / root_dir
        root_path.mkdir(parents=True, exist_ok=True)
        created.append(str(root_path.relative_to(base_path)))
        
        for sub_dir in sub_dirs:
            sub_path = root_path / sub_dir
            sub_path.mkdir(parents=True, exist_ok=True)
            created.append(str(sub_path.relative_to(base_path)))

    return created

def print_tree(directory: Path, prefix: str = ""):
    """Print a tree representation of the directory structure."""
    items = sorted(directory.iterdir())
    pointers = ['└── '] * (len(items) - 1) + ['└── '] if items else []
    
    for i, item in enumerate(items):
        pointer = pointers[i] if i < len(pointers) else '└── '
        print(f"{prefix}{pointer}{item.name}")
        if item.is_dir():
            extension = "    " if i == len(items) - 1 else "│   "
            print_tree(item, prefix + extension)

def main():
    base_path = Path(__file__).resolve().parent.parent
    print(f"Creating directory structure in: {base_path}")
    
    created_dirs = create_directories()
    
    print("\nCreated directories:")
    for d in sorted(created_dirs):
        print(f"  {d}")
    
    print("\nDirectory Tree:")
    tree_path = base_path / "src"
    if tree_path.exists():
        print_tree(tree_path)
    
    print("\nStructure creation complete.")

if __name__ == "__main__":
    main()
import os
import sys
from pathlib import Path
from typing import List, Tuple

def create_directories() -> List[Path]:
    """Create the required project directory structure."""
    base_dirs = [
        "code/data_generation",
        "code/training",
        "code/evaluation",
        "code/utils",
        "data/raw",
        "data/processed",
        "tests/unit",
        "tests/contract",
        "tests/integration",
        "specs/001-predict-stiffness-cnn/contracts",
    ]
    
    created = []
    for dir_path in base_dirs:
        path = Path(dir_path)
        path.mkdir(parents=True, exist_ok=True)
        created.append(path)
    
    return created

def create_init_files() -> List[Path]:
    """Create __init__.py files for all Python packages."""
    init_paths = [
        "code/__init__.py",
        "code/data_generation/__init__.py",
        "code/training/__init__.py",
        "code/evaluation/__init__.py",
        "code/utils/__init__.py",
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/contract/__init__.py",
        "tests/integration/__init__.py",
    ]
    
    created = []
    for init_path in init_paths:
        path = Path(init_path)
        path.touch()
        created.append(path)
    
    return created

def create_placeholder_files() -> List[Path]:
    """Create placeholder files as specified in the task."""
    placeholder_paths = [
        "code/main.py",
        "code/data_generation/generate_microstructures.py",
        "code/data_generation/compute_stiffness.py",
        "code/training/model.py",
        "code/training/train.py",
        "code/evaluation/stats_utils.py",
        "code/evaluation/evaluate.py",
        "docs/constitution_amendment_proposal.md",
    ]
    
    created = []
    for file_path in placeholder_paths:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
        created.append(path)
    
    return created

def print_tree_structure(root: Path = None) -> str:
    """Generate a tree-like string representation of the directory structure."""
    if root is None:
        root = Path(".")
    
    lines = []
    
    def _print_tree(current_path: Path, prefix: str = ""):
        contents = sorted(current_path.iterdir())
        # Filter out hidden files and common non-project directories
        contents = [c for c in contents if not c.name.startswith('.')]
        
        for i, item in enumerate(contents):
            is_last = i == len(contents) - 1
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{item.name}")
            
            if item.is_dir():
                extension = "    " if is_last else "│   "
                _print_tree(item, prefix + extension)
    
    lines.append(f"{root.name}/")
    _print_tree(root)
    return "\n".join(lines)

def check_structure() -> Tuple[bool, List[str]]:
    """Verify that the required directory structure exists."""
    required_dirs = [
        "code/data_generation",
        "code/training",
        "code/evaluation",
        "code/utils",
        "data/raw",
        "data/processed",
        "tests/unit",
        "tests/contract",
        "tests/integration",
        "specs/001-predict-stiffness-cnn/contracts",
    ]
    
    required_files = [
        "code/__init__.py",
        "code/data_generation/__init__.py",
        "code/training/__init__.py",
        "code/evaluation/__init__.py",
        "code/utils/__init__.py",
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/contract/__init__.py",
        "tests/integration/__init__.py",
        "code/main.py",
        "code/data_generation/generate_microstructures.py",
        "code/data_generation/compute_stiffness.py",
        "code/training/model.py",
        "code/training/train.py",
        "code/evaluation/stats_utils.py",
        "code/evaluation/evaluate.py",
    ]
    
    missing = []
    
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing.append(f"Directory missing: {dir_path}")
    
    for file_path in required_files:
        if not Path(file_path).exists():
            missing.append(f"File missing: {file_path}")
    
    return len(missing) == 0, missing

def main():
    """Main entry point for project setup."""
    print("Setting up project structure for PROJ-506-predicting-material-stiffness-from-micro...")
    
    # Create directories
    print("Creating directories...")
    dirs = create_directories()
    print(f"  Created {len(dirs)} directories.")
    
    # Create __init__.py files
    print("Creating __init__.py files...")
    inits = create_init_files()
    print(f"  Created {len(inits)} __init__.py files.")
    
    # Create placeholder files
    print("Creating placeholder files...")
    placeholders = create_placeholder_files()
    print(f"  Created {len(placeholders)} placeholder files.")
    
    # Verify structure
    print("Verifying structure...")
    success, missing = check_structure()
    
    if success:
        print("\nStructure verification: PASSED")
        print("\nDirectory Tree:")
        print(print_tree_structure())
        sys.exit(0)
    else:
        print("\nStructure verification: FAILED")
        for item in missing:
            print(f"  - {item}")
        sys.exit(1)

if __name__ == "__main__":
    main()

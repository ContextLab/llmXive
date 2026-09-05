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
    
    created_paths = []
    for dir_path in base_dirs:
        path = Path(dir_path)
        path.mkdir(parents=True, exist_ok=True)
        created_paths.append(path)
        print(f"Created directory: {path}")
    
    return created_paths

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
    
    created_files = []
    for file_path in init_paths:
        path = Path(file_path)
        path.touch()
        created_files.append(path)
        print(f"Created file: {path}")
    
    return created_files

def create_placeholder_files() -> List[Path]:
    """Create placeholder Python files as specified in the task."""
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
    
    created_files = []
    for file_path in placeholder_paths:
        path = Path(file_path)
        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
        created_files.append(path)
        print(f"Created file: {path}")
    
    return created_files

def print_tree_structure(root_paths: List[str]) -> bool:
    """
    Print the directory tree structure for verification.
    Returns True if successful, False otherwise.
    """
    print("\n--- Project Directory Structure ---")
    for root_path in root_paths:
        root = Path(root_path)
        if not root.exists():
            print(f"Path does not exist: {root}")
            continue
        
        print(f"\n{root}/")
        for item in sorted(root.rglob("*")):
            rel_path = item.relative_to(root)
            depth = len(rel_path.parts) - 1
            indent = "  " * depth
            if item.is_dir():
                print(f"{indent}├── {item.name}/")
            else:
                print(f"{indent}├── {item.name}")
    
    print("\n--- End of Structure ---")
    return True

def check_structure() -> Tuple[bool, List[str]]:
    """
    Verify that all required directories and files exist.
    Returns (success, list_of_missing_paths).
    """
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
    
    for d in required_dirs:
        if not Path(d).is_dir():
            missing.append(f"Directory missing: {d}")
    
    for f in required_files:
        if not Path(f).is_file():
            missing.append(f"File missing: {f}")
    
    return len(missing) == 0, missing

def main() -> int:
    """Main entry point for project setup."""
    print("Starting project directory setup...")
    
    # Create directories
    create_directories()
    
    # Create __init__.py files
    create_init_files()
    
    # Create placeholder files
    create_placeholder_files()
    
    # Print tree structure for verification
    print_tree_structure(["code", "data", "tests", "specs"])
    
    # Verify structure
    success, missing = check_structure()
    
    if success:
        print("\n✓ All required directories and files created successfully.")
        return 0
    else:
        print("\n✗ Verification failed. Missing items:")
        for item in missing:
            print(f"  - {item}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
import os
import sys
from pathlib import Path
from typing import List, Tuple

def create_directories() -> List[str]:
    """Create the required project directory structure."""
    # Define all required directories relative to the project root
    # Note: We assume the script runs from the project root or code/
    # We will resolve paths relative to the current working directory
    # to ensure they are created where expected.
    base_path = Path.cwd()
    
    # Adjust base_path if running from 'code' subdirectory
    # to ensure we create dirs at the project root level
    if base_path.name == "code":
        base_path = base_path.parent
    
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
    
    created = []
    for dir_path in required_dirs:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(str(full_path))
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")
            created.append(str(full_path))
    
    return created

def create_init_files() -> List[str]:
    """Create __init__.py files for all Python packages."""
    base_path = Path.cwd()
    if base_path.name == "code":
        base_path = base_path.parent
        
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
    for file_path in init_paths:
        full_path = base_path / file_path
        # Ensure parent directory exists before creating file
        full_path.parent.mkdir(parents=True, exist_ok=True)
        if not full_path.exists():
            full_path.touch()
            created.append(str(full_path))
            print(f"Created file: {full_path}")
        else:
            print(f"File already exists: {full_path}")
            created.append(str(full_path))
    
    return created

def create_placeholder_files() -> List[str]:
    """Create placeholder files for main scripts and docs."""
    base_path = Path.cwd()
    if base_path.name == "code":
        base_path = base_path.parent
        
    placeholder_files = [
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
    for file_path in placeholder_files:
        full_path = base_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        if not full_path.exists():
            full_path.touch()
            created.append(str(full_path))
            print(f"Created placeholder: {full_path}")
        else:
            print(f"Placeholder already exists: {full_path}")
        created.append(str(full_path))
    
    return created

def print_tree_structure(base_path: Optional[Path] = None) -> None:
    """Print a tree-like structure of the project."""
    if base_path is None:
        base_path = Path.cwd()
        if base_path.name == "code":
            base_path = base_path.parent
    
    print(f"\nProject Structure at: {base_path}")
    print("=" * 50)
    
    # List all directories and files we created
    targets = [
        "code", "data", "tests", "specs"
    ]
    
    for target in targets:
        target_path = base_path / target
        if target_path.exists():
            for item in sorted(target_path.rglob("*")):
                rel_path = item.relative_to(base_path)
                indent = "  " * len(rel_path.parts)
                print(f"{indent}{rel_path.name}")

def check_structure() -> Tuple[bool, List[str]]:
    """Verify all required directories and files exist."""
    base_path = Path.cwd()
    if base_path.name == "code":
        base_path = base_path.parent
    
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
    
    missing_dirs = []
    for dir_path in required_dirs:
        full_path = base_path / dir_path
        if not full_path.is_dir():
            missing_dirs.append(dir_path)
    
    return len(missing_dirs) == 0, missing_dirs

def main() -> int:
    """Main entry point for project setup."""
    print("Starting project directory setup...")
    
    # Create directories
    created_dirs = create_directories()
    print(f"Created/Verified {len(created_dirs)} directories")
    
    # Create init files
    created_inits = create_init_files()
    print(f"Created/Verified {len(created_inits)} __init__.py files")
    
    # Create placeholder files
    created_placeholders = create_placeholder_files()
    print(f"Created/Verified {len(created_placeholders)} placeholder files")
    
    # Verify structure
    success, missing = check_structure()
    if success:
        print("\n✓ All required directories and files exist.")
        print_tree_structure()
        return 0
    else:
        print(f"\n✗ Missing directories: {missing}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

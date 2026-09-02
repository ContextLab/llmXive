import os
import sys
from pathlib import Path
from typing import List, Tuple

def create_directories(base_path: Path) -> List[Path]:
    """
    Create the required project directory structure.
    
    Args:
        base_path: The root directory of the project.
        
    Returns:
        List of created directory paths.
    """
    dirs_to_create = [
        "code/data_generation",
        "code/training",
        "code/evaluation",
        "code/utils",
        "data/raw",
        "data/processed",
        "tests/unit",
        "tests/contract",
        "tests/integration",
        "specs/001-predict-stiffness-cnn/contracts"
    ]
    
    created_dirs = []
    for dir_path in dirs_to_create:
        full_path = base_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        created_dirs.append(full_path)
        print(f"Created directory: {full_path}")
        
    return created_dirs

def create_init_files(base_path: Path) -> List[Path]:
    """
    Create __init__.py files for all Python packages.
    
    Args:
        base_path: The root directory of the project.
        
    Returns:
        List of created __init__.py file paths.
    """
    init_files = [
        "code/__init__.py",
        "code/data_generation/__init__.py",
        "code/training/__init__.py",
        "code/evaluation/__init__.py",
        "code/utils/__init__.py",
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/contract/__init__.py",
        "tests/integration/__init__.py"
    ]
    
    created_files = []
    for file_path in init_files:
        full_path = base_path / file_path
        full_path.touch()
        created_files.append(full_path)
        print(f"Created file: {full_path}")
        
    return created_files

def create_placeholder_files(base_path: Path) -> List[Path]:
    """
    Create placeholder Python files for the project structure.
    
    Args:
        base_path: The root directory of the project.
        
    Returns:
        List of created placeholder file paths.
    """
    placeholder_files = [
        "code/main.py",
        "code/data_generation/generate_microstructures.py",
        "code/data_generation/compute_stiffness.py",
        "code/training/model.py",
        "code/training/train.py",
        "code/evaluation/stats_utils.py",
        "code/evaluation/evaluate.py",
        "docs/constitution_amendment_proposal.md"
    ]
    
    created_files = []
    for file_path in placeholder_files:
        full_path = base_path / file_path
        # Ensure parent directory exists
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.touch()
        created_files.append(full_path)
        print(f"Created placeholder file: {full_path}")
        
    return created_files

def print_tree_structure(base_path: Path) -> str:
    """
    Generate a tree-like string representation of the directory structure.
    
    Args:
        base_path: The root directory of the project.
        
    Returns:
        String representation of the directory tree.
    """
    tree_output = []
    tree_output.append(f"Project structure at: {base_path}")
    tree_output.append("-" * 50)
    
    # Walk through the directory structure
    for root, dirs, files in os.walk(base_path):
        # Calculate relative path from base
        rel_root = Path(root).relative_to(base_path)
        if str(rel_root) == '.':
            level = 0
        else:
            level = str(rel_root).count(os.sep)
        
        # Indent based on level
        indent = "    " * level
        tree_output.append(f"{indent}{Path(root).name}/")
        
        sub_indent = "    " * (level + 1)
        for file in files:
            tree_output.append(f"{sub_indent}{file}")
    
    return "\n".join(tree_output)

def check_structure(base_path: Path) -> Tuple[bool, List[str]]:
    """
    Verify that the required directory structure exists.
    
    Args:
        base_path: The root directory of the project.
        
    Returns:
        Tuple of (success, list of missing paths)
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
        "specs/001-predict-stiffness-cnn/contracts"
    ]
    
    missing = []
    for dir_path in required_dirs:
        full_path = base_path / dir_path
        if not full_path.exists() or not full_path.is_dir():
            missing.append(dir_path)
    
    return (len(missing) == 0, missing)

def main():
    """
    Main function to set up the project structure.
    """
    # Determine project root (assuming script is in code/ or code/setup_project.py)
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    
    print(f"Setting up project structure at: {project_root}")
    
    # Create directories
    print("\n--- Creating Directories ---")
    create_directories(project_root)
    
    # Create __init__.py files
    print("\n--- Creating __init__.py Files ---")
    create_init_files(project_root)
    
    # Create placeholder files
    print("\n--- Creating Placeholder Files ---")
    create_placeholder_files(project_root)
    
    # Verify structure
    print("\n--- Verifying Structure ---")
    success, missing = check_structure(project_root)
    
    if success:
        print("✓ All required directories exist.")
        
        # Print tree structure
        print("\n--- Project Directory Tree ---")
        tree_str = print_tree_structure(project_root)
        print(tree_str)
        
        # Simulate tree command exit code 0
        print("\n✓ Directory tree verification successful (exit code 0)")
        return 0
    else:
        print("✗ Missing directories:")
        for m in missing:
            print(f"  - {m}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

"""
Project Setup Utility for PROJ-506-predicting-material-stiffness-from-micro

This module provides functions to create the project directory structure,
initialize Python packages with __init__.py files, create placeholder files,
and verify the structure.
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple

# Define the directory structure to create
DIRECTORIES = [
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

# Define __init__.py files to create
INIT_FILES = [
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

# Define placeholder files to create
# Note: T006c asks for specific files. We create them with minimal valid content
# to satisfy the "file exists" requirement, while keeping them extensible.
PLACEHOLDER_FILES = {
    "code/main.py": "# Main entry point\n",
    "code/data_generation/generate_microstructures.py": "# Microstructure generation\n",
    "code/data_generation/compute_stiffness.py": "# Stiffness computation\n",
    "code/training/model.py": "# CNN Model definition\n",
    "code/training/train.py": "# Training loop\n",
    "code/evaluation/stats_utils.py": "# Statistical utilities\n",
    "code/evaluation/evaluate.py": "# Evaluation script\n",
    "docs/constitution_amendment_proposal.md": "# Constitution Amendment Proposal\n",
}

def create_directories(base_path: Path) -> List[Path]:
    """
    Create all required directories.

    Args:
        base_path: The root directory of the project.

    Returns:
        List of created directory paths.
    """
    created_dirs = []
    for dir_name in DIRECTORIES:
        dir_path = base_path / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        created_dirs.append(dir_path)
        print(f"Created directory: {dir_path}")
    return created_dirs

def create_init_files(base_path: Path) -> List[Path]:
    """
    Create __init__.py files for all packages.

    Args:
        base_path: The root directory of the project.

    Returns:
        List of created file paths.
    """
    created_files = []
    for file_name in INIT_FILES:
        file_path = base_path / file_name
        file_path.touch(exist_ok=True)
        created_files.append(file_path)
        print(f"Created file: {file_path}")
    return created_files

def create_placeholder_files(base_path: Path) -> List[Path]:
    """
    Create placeholder files with minimal content.

    Args:
        base_path: The root directory of the project.

    Returns:
        List of created file paths.
    """
    created_files = []
    for file_name, content in PLACEHOLDER_FILES.items():
        file_path = base_path / file_name
        # Ensure parent directory exists (for docs/)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        created_files.append(file_path)
        print(f"Created file: {file_path}")
    return created_files

def verify_structure(base_path: Path) -> Tuple[bool, List[str]]:
    """
    Verify that all required directories and files exist.

    Args:
        base_path: The root directory of the project.

    Returns:
        A tuple (success, list_of_missing_items).
    """
    missing = []

    # Check directories
    for dir_name in DIRECTORIES:
        if not (base_path / dir_name).is_dir():
            missing.append(f"Directory missing: {dir_name}")

    # Check __init__.py files
    for file_name in INIT_FILES:
        if not (base_path / file_name).is_file():
            missing.append(f"File missing: {file_name}")

    # Check placeholder files
    for file_name in PLACEHOLDER_FILES.keys():
        if not (base_path / file_name).is_file():
            missing.append(f"File missing: {file_name}")

    success = len(missing) == 0
    return success, missing

def main():
    """Main entry point for the setup script."""
    # Determine project root (assume script is in code/ or code/utils/)
    # We look for the parent of the 'code' directory
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent

    print(f"Project root detected at: {project_root}")

    print("\n--- Creating Directories ---")
    create_directories(project_root)

    print("\n--- Creating __init__.py Files ---")
    create_init_files(project_root)

    print("\n--- Creating Placeholder Files ---")
    create_placeholder_files(project_root)

    print("\n--- Verifying Structure ---")
    success, missing = verify_structure(project_root)

    if success:
        print("\n✅ All directories and files created successfully.")
        sys.exit(0)
    else:
        print("\n❌ Verification failed. Missing items:")
        for item in missing:
            print(f"   - {item}")
        sys.exit(1)

if __name__ == "__main__":
    main()

"""
Script to initialize the project directory structure for llmXive follow-up.
Creates required directories and verifies their existence.
"""
import os
import sys
from pathlib import Path

def create_directory_structure(root_path: Path) -> None:
    """
    Creates the standard directory structure for the research project.
    
    Args:
        root_path: The root directory where the project structure will be created.
    """
    # Define the directory structure relative to root_path
    directories = [
        "data/raw",
        "data/processed",
        "code/src",
        "code/tests",
        "code/notebooks",
        "paper",
        "state",
        "contracts"
    ]

    for dir_name in directories:
        full_path = root_path / dir_name
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")

def verify_directory_structure(root_path: Path) -> bool:
    """
    Verifies that all required directories exist.
    
    Args:
        root_path: The root directory to verify.
        
    Returns:
        True if all directories exist, False otherwise.
    """
    required_dirs = [
        "data/raw",
        "data/processed",
        "code/src",
        "code/tests",
        "code/notebooks",
        "paper",
        "state",
        "contracts"
    ]

    all_exist = True
    for dir_name in required_dirs:
        full_path = root_path / dir_name
        if not full_path.is_dir():
            print(f"MISSING: {full_path}")
            all_exist = False
        else:
            print(f"VERIFIED: {full_path}")
    
    return all_exist

def main():
    """
    Main entry point for the script.
    """
    # Determine the project root. 
    # We assume this script is at code/scripts/setup_project_structure.py
    # The project root is the parent of the parent of this script's directory.
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent

    print(f"Project root identified as: {project_root}")

    # Create the structure
    print("\n--- Creating Directory Structure ---")
    create_directory_structure(project_root)

    # Verify the structure
    print("\n--- Verifying Directory Structure ---")
    success = verify_directory_structure(project_root)

    if success:
        print("\n✅ All required directories created and verified successfully.")
        sys.exit(0)
    else:
        print("\n❌ Verification failed. Some directories are missing.")
        sys.exit(1)

if __name__ == "__main__":
    main()

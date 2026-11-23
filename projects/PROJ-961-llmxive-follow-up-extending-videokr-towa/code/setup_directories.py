"""
Project initialization script for llmXive pipeline.
Creates the required directory structure and .gitkeep files.
"""
import os
import sys
from pathlib import Path
from typing import List

from utils.config import get_project_root, ensure_dir


def create_directory(path: Path) -> bool:
    """
    Create a directory if it does not exist.
    
    Args:
        path: The directory path to create.
        
    Returns:
        True if directory was created or already exists, False otherwise.
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except OSError as e:
        print(f"Error creating directory {path}: {e}", file=sys.stderr)
        return False


def verify_directory(path: Path) -> bool:
    """
    Verify that a directory exists.
    
    Args:
        path: The directory path to verify.
        
    Returns:
        True if directory exists, False otherwise.
    """
    return path.is_dir()


def ensure_directory_structure() -> bool:
    """
    Create and verify the full project directory structure.
    
    Returns:
        True if all directories were created and verified successfully,
        False otherwise.
    """
    project_root = get_project_root()
    
    # Define all required directories relative to project root
    required_dirs: List[Path] = [
        project_root / "code",
        project_root / "tests",
        project_root / "data",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "code" / "ingest",
        project_root / "code" / "analysis",
        project_root / "code" / "utils",
        project_root / "tests" / "unit",
        project_root / "tests" / "integration",
    ]
    
    all_success = True
    
    for dir_path in required_dirs:
        # Create directory
        if not create_directory(dir_path):
            all_success = False
            continue
        
        # Verify directory exists
        if not verify_directory(dir_path):
            print(f"Verification failed: Directory {dir_path} does not exist after creation.", file=sys.stderr)
            all_success = False
            continue
        
        # Create .gitkeep file to ensure directory is tracked by git
        gitkeep_path = dir_path / ".gitkeep"
        try:
            gitkeep_path.touch(exist_ok=True)
            print(f"Created: {dir_path} with .gitkeep")
        except OSError as e:
            print(f"Error creating .gitkeep in {dir_path}: {e}", file=sys.stderr)
            all_success = False
    
    if all_success:
        print("✓ All project directories created and verified successfully.")
    else:
        print("✗ Some directories failed to create or verify.", file=sys.stderr)
    
    return all_success


def main() -> int:
    """
    Main entry point for the directory initialization script.
    
    Returns:
        Exit code: 0 for success, 1 for failure.
    """
    print("Initializing project directory structure for llmXive...")
    
    success = ensure_directory_structure()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
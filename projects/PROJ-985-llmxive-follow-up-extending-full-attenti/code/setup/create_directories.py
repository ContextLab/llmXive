"""
T001a: Create base project directories and verify their existence.

This script creates the required directory structure for the llmXive project
and verifies that all directories were created successfully.
"""
import os
import sys
from pathlib import Path
from typing import List

def get_project_root() -> Path:
    """Get the project root directory (parent of code/setup)."""
    return Path(__file__).resolve().parent.parent.parent

def create_directories(root: Path, dir_paths: List[str]) -> List[str]:
    """
    Create directories relative to the project root.
    
    Args:
        root: Project root path
        dir_paths: List of relative directory paths to create
        
    Returns:
        List of successfully created directory paths
    """
    created = []
    for dir_path in dir_paths:
        full_path = root / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(str(full_path))
            print(f"Created: {full_path}")
        except Exception as e:
            print(f"Failed to create {full_path}: {e}", file=sys.stderr)
    return created

def verify_directories(root: Path, dir_paths: List[str]) -> bool:
    """
    Verify that all required directories exist.
    
    Args:
        root: Project root path
        dir_paths: List of relative directory paths to verify
        
    Returns:
        True if all directories exist, False otherwise
    """
    all_exist = True
    for dir_path in dir_paths:
        full_path = root / dir_path
        if not os.path.isdir(full_path):
            print(f"MISSING: {full_path}", file=sys.stderr)
            all_exist = False
        else:
            print(f"Verified: {full_path}")
    return all_exist

def main():
    """Main entry point for directory creation and verification."""
    root = get_project_root()
    print(f"Project root: {root}")
    
    # Required directories as per T001a
    required_dirs = [
        "code",
        "tests",
        "data",
        "code/lib",
        "code/data",
        "code/models",
        "code/evaluation",
        "data/results",
        "data/logs",
        "data/intermediate",
        "data/config"
    ]
    
    # Create directories
    print("\n--- Creating directories ---")
    created = create_directories(root, required_dirs)
    
    # Verify directories
    print("\n--- Verifying directories ---")
    success = verify_directories(root, required_dirs)
    
    if success:
        print("\n✓ All required directories created and verified successfully.")
        return 0
    else:
        print("\n✗ Some directories are missing. Check error messages above.", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())

"""
Task T001c: Create and verify the 'data/interim' directory.

This script ensures the existence of the data/interim directory as required
by the project setup phase. It creates the directory if it does not exist
and verifies its presence programmatically.
"""
import os
import sys
from pathlib import Path

def create_interim_directory(base_path: Path) -> bool:
    """
    Create the 'data/interim' directory if it doesn't exist.
    
    Args:
        base_path: The root path of the project.
        
    Returns:
        True if directory was created or already exists, False otherwise.
    """
    interim_dir = base_path / "data" / "interim"
    try:
        interim_dir.mkdir(parents=True, exist_ok=True)
        return True
    except OSError as e:
        print(f"Error creating directory {interim_dir}: {e}", file=sys.stderr)
        return False

def verify_interim_directory(base_path: Path) -> bool:
    """
    Verify that the 'data/interim' directory exists and is a directory.
    
    Args:
        base_path: The root path of the project.
        
    Returns:
        True if directory exists and is a directory, False otherwise.
    """
    interim_dir = base_path / "data" / "interim"
    is_valid = interim_dir.exists() and interim_dir.is_dir()
    return is_valid

def main():
    """Main entry point for the script."""
    # Determine project root (assuming script is in code/)
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    interim_path = project_root / "data" / "interim"

    print(f"Project Root: {project_root}")
    print(f"Target Directory: {interim_path}")

    # Create the directory
    print("Creating 'data/interim' directory...")
    if create_interim_directory(project_root):
        print(f"Successfully ensured existence of {interim_path}")
    else:
        print(f"Failed to create {interim_path}", file=sys.stderr)
        sys.exit(1)

    # Verify the directory
    print("Verifying directory existence...")
    if verify_interim_directory(project_root):
        print(f"Verification PASSED: {interim_path} exists and is a directory.")
        print(f"Directory permissions: {oct(interim_path.stat().st_mode)[-3:]}")
        print(f"Directory size (approx): {sum(1 for _ in interim_path.iterdir())} items")
    else:
        print(f"Verification FAILED: {interim_path} does not exist or is not a directory.", file=sys.stderr)
        sys.exit(1)

    print("Task T001c completed successfully.")

if __name__ == "__main__":
    main()

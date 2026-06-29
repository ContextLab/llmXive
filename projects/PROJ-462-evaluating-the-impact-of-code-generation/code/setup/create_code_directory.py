"""
T001a: Create code/ directory at repository root.

This script creates the code/ directory structure required for the
llmXive automated science pipeline implementation.

Usage:
    python code/setup/create_code_directory.py
"""
import os
import sys
from pathlib import Path


def create_code_directory():
    """Create the code/ directory at the repository root."""
    # Get the repository root (parent of the code/ directory)
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent
    
    code_dir = repo_root / "code"
    
    if code_dir.exists():
        print(f"Directory already exists: {code_dir}")
        return True
    
    try:
        code_dir.mkdir(parents=True, exist_ok=True)
        print(f"Successfully created directory: {code_dir}")
        return True
    except OSError as e:
        print(f"Error creating directory {code_dir}: {e}", file=sys.stderr)
        return False


def main():
    """Main entry point for directory creation."""
    print("T001a: Creating code/ directory at repository root...")
    success = create_code_directory()
    
    if success:
        print("T001a completed successfully.")
        return 0
    else:
        print("T001a failed.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
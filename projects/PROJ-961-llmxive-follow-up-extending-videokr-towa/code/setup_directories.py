"""
Setup script to create and verify the core project directory structure.
Implements T001b: Create code/ingest/, code/analysis/, code/utils/ subdirectories.
Also handles T001a (root directories) and T001c (test directories) for completeness
as they are interdependent setup tasks.
"""
import os
import sys
from pathlib import Path
from typing import List, Tuple

def get_project_root() -> Path:
    """
    Determine the project root directory.
    Assumes the script is run from the repository root or code/ directory.
    """
    current = Path.cwd()
    # Check if we are in code/
    if current.name == "code":
        return current.parent
    # Check if we are in root (look for code/ sibling)
    if (current / "code").is_dir():
        return current
    # Fallback: look for a marker or assume current
    return current

def create_directory(path: Path) -> bool:
    """
    Create a directory if it does not exist.
    Returns True if successful, False otherwise.
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except OSError as e:
        print(f"Error creating directory {path}: {e}", file=sys.stderr)
        return False

def verify_directory(path: Path) -> bool:
    """
    Verify that a directory exists using os.path.exists.
    Returns True if it exists and is a directory, False otherwise.
    """
    if not os.path.exists(path):
        print(f"Verification Failed: Directory {path} does not exist.", file=sys.stderr)
        return False
    if not os.path.isdir(path):
        print(f"Verification Failed: {path} exists but is not a directory.", file=sys.stderr)
        return False
    return True

def ensure_directory_structure(root: Path) -> Tuple[bool, List[str]]:
    """
    Create and verify the required directory structure.
    
    Returns:
        Tuple of (success: bool, errors: List[str])
    """
    errors = []
    
    # Define required directories relative to root
    required_dirs = [
        # Phase 1: Setup (Root) - T001a
        "code",
        "tests",
        "data",
        
        # Phase 1: Setup (Subdirectories) - T001b
        "code/ingest",
        "code/analysis",
        "code/utils",
        
        # Phase 1: Setup (Test Subdirectories) - T001c
        "tests/unit",
        "tests/integration",
        
        # Data Subdirectories for T008a/b (often created alongside)
        "data/raw",
        "data/processed",
    ]

    print(f"Project Root identified: {root}")
    print("Creating and verifying directory structure...")

    for dir_name in required_dirs:
        target_path = root / dir_name
        
        # Create if missing
        if not target_path.exists():
            print(f"  Creating: {dir_name} ...", end=" ")
            if create_directory(target_path):
                print("OK")
            else:
                errors.append(f"Failed to create {dir_name}")
        else:
            print(f"  Exists: {dir_name}")

        # Verify
        if not verify_directory(target_path):
            errors.append(f"Verification failed for {dir_name}")

    success = len(errors) == 0
    return success, errors

def main():
    """
    Entry point for the setup script.
    Exits with code 1 if any directory creation or verification fails.
    """
    root = get_project_root()
    success, errors = ensure_directory_structure(root)

    if errors:
        print("\n❌ Setup Failed:")
        for err in errors:
            print(f"   - {err}")
        sys.exit(1)
    else:
        print("\n✅ All directories created and verified successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()
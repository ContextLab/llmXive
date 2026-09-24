"""
Script to create and verify the project directory structure.
This implements task T001a (code/) and serves as the foundation for T001b-T001e.
Ensures idempotency: creates directories if they do not exist and verifies writability.
"""
import os
import sys
import argparse
from pathlib import Path
from typing import List, Tuple, Optional

# Define the required directories relative to the project root
REQUIRED_DIRS = [
    "code",
    "tests",
    "data/raw",
    "data/processed",
    "results"
]

def ensure_directory_exists(dir_path: Path) -> Tuple[bool, str]:
    """
    Creates a directory if it does not exist and verifies it is writable.
    
    Args:
        dir_path: Path object representing the directory to create/verify.
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        # Create directory if it doesn't exist (parents=True ensures parent dirs are created too)
        dir_path.mkdir(parents=True, exist_ok=True)
        
        # Verify writability by attempting to create a temporary file
        test_file = dir_path / ".write_test"
        try:
            test_file.touch(exist_ok=True)
            test_file.unlink() # Remove the test file
            return True, f"Directory '{dir_path}' exists and is writable."
        except (PermissionError, OSError) as e:
            return False, f"Directory '{dir_path}' exists but is NOT writable: {e}"
            
    except Exception as e:
        return False, f"Failed to create directory '{dir_path}': {e}"

def main():
    parser = argparse.ArgumentParser(
        description="Create and verify project directory structure (T001a-T001e)."
    )
    parser.add_argument(
        "--project-root",
        type=str,
        default=".",
        help="Path to the project root directory (default: current directory)"
    )
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    print(f"Project Root: {project_root}")
    
    all_success = True
    failed_dirs: List[Tuple[str, str]] = []

    for rel_dir in REQUIRED_DIRS:
        full_path = project_root / rel_dir
        success, message = ensure_directory_exists(full_path)
        print(f"[{'OK' if success else 'FAIL'}] {message}")
        
        if not success:
            all_success = False
            failed_dirs.append((rel_dir, message))

    print("\n" + "="*50)
    if all_success:
        print("SUCCESS: All required directories created and verified.")
        sys.exit(0)
    else:
        print("FAILURE: The following directories failed verification:")
        for d, msg in failed_dirs:
            print(f"  - {d}: {msg}")
        sys.exit(1)

if __name__ == "__main__":
    main()
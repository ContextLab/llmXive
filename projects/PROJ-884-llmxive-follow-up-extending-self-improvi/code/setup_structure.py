import os
import sys
import argparse
from pathlib import Path
from typing import List

def setup_code_directories(base_path: Path) -> bool:
    """
    Creates the required code directory hierarchy for the project.
    
    Creates:
    - code/dataset
    - code/symbolic
    - code/bes
    - code/analysis
    - code/utils
    
    Args:
        base_path: The project root directory path.
        
    Returns:
        True if all directories were created successfully and are writable.
        
    Raises:
        RuntimeError: If any directory cannot be created or verified.
    """
    sub_dirs = [
        "dataset",
        "symbolic",
        "bes",
        "analysis",
        "utils"
    ]
    
    code_root = base_path / "code"
    code_root.mkdir(parents=True, exist_ok=True)
    
    # Verify code root is writable
    try:
        test_file = code_root / ".write_test"
        test_file.touch()
        test_file.unlink()
    except OSError as e:
        raise RuntimeError(f"Code root directory '{code_root}' is not writable: {e}")
    
    for subdir in sub_dirs:
        target_dir = code_root / subdir
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            # Verify the specific subdirectory is writable
            test_file = target_dir / ".write_test"
            test_file.touch()
            test_file.unlink()
        except OSError as e:
            raise RuntimeError(f"Failed to create or verify writability of '{target_dir}': {e}")
    
    return True

def main():
    """Entry point for CLI execution."""
    parser = argparse.ArgumentParser(
        description="Setup the code directory hierarchy for the llmXive project."
    )
    parser.add_argument(
        "--base-path",
        type=Path,
        default=Path("."),
        help="Path to the project root (default: current directory)"
    )
    
    args = parser.parse_args()
    
    try:
        success = setup_code_directories(args.base_path)
        if success:
            print("Successfully created and verified code directory hierarchy:")
            print(f"  - code/dataset")
            print(f"  - code/symbolic")
            print(f"  - code/bes")
            print(f"  - code/analysis")
            print(f"  - code/utils")
            sys.exit(0)
        else:
            print("Failed to setup directories.")
            sys.exit(1)
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

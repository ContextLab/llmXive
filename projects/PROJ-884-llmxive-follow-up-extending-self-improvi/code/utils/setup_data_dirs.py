import os
import sys
import argparse
from pathlib import Path
from typing import List, Tuple

def get_project_root() -> Path:
    """
    Determine the project root directory.
    Assumes the script is run from the project root or a subdirectory.
    Looks for a 'data' directory or 'tasks.md' to identify the root.
    """
    current = Path.cwd()
    # Walk up until we find a marker or hit the filesystem root
    while current != current.parent:
        if (current / "tasks.md").exists() or (current / "data").exists():
            return current
        current = current.parent
    
    # Fallback to current directory if no marker found
    return Path.cwd()

def setup_data_directories(base_path: Path, verbose: bool = True) -> Tuple[bool, List[str]]:
    """
    Create the required data directory hierarchy:
    - data/raw (for immutable puzzles)
    - data/processed (for logs/results)
    
    Args:
        base_path: The project root path
        verbose: If True, print status messages
    
    Returns:
        Tuple of (success_flag, list_of_created_paths)
    """
    data_root = base_path / "data"
    raw_dir = data_root / "raw"
    processed_dir = data_root / "processed"
    
    created_paths = []
    errors = []
    
    directories_to_create = [data_root, raw_dir, processed_dir]
    
    for dir_path in directories_to_create:
        try:
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                if verbose:
                    print(f"Created directory: {dir_path}")
                created_paths.append(str(dir_path))
            else:
                if verbose:
                    print(f"Directory already exists: {dir_path}")
        
            # Verify writability
            test_file = dir_path / ".write_test"
            try:
                test_file.touch(exist_ok=True)
                test_file.unlink()
                if verbose:
                    print(f"Verified writable: {dir_path}")
            except (OSError, PermissionError) as e:
                error_msg = f"Directory exists but is not writable: {dir_path} ({e})"
                errors.append(error_msg)
                if verbose:
                    print(f"ERROR: {error_msg}", file=sys.stderr)
        
        except (OSError, PermissionError) as e:
            error_msg = f"Failed to create directory {dir_path}: {e}"
            errors.append(error_msg)
            if verbose:
                print(f"ERROR: {error_msg}", file=sys.stderr)
    
    success = len(errors) == 0
    return success, created_paths

def main():
    parser = argparse.ArgumentParser(
        description="Setup data directory hierarchy for the llmXive project."
    )
    parser.add_argument(
        "--project-root",
        type=str,
        default=None,
        help="Path to the project root. If not provided, auto-detected."
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress output messages."
    )
    
    args = parser.parse_args()
    
    base_path = Path(args.project_root) if args.project_root else get_project_root()
    verbose = not args.quiet
    
    if verbose:
        print(f"Project root detected as: {base_path}")
    
    success, created = setup_data_directories(base_path, verbose=verbose)
    
    if success:
        if verbose:
            print("\nSetup successful. Data directories created/verified:")
            for p in created:
                print(f"  - {p}")
        sys.exit(0)
    else:
        if verbose:
            print("\nSetup failed. Errors encountered:", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

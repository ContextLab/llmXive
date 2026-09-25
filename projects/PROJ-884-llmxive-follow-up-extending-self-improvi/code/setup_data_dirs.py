"""
Setup script for T004: Data Directory Structure.

Creates and verifies the data directory hierarchy:
- data/raw: for immutable puzzles
- data/processed: for logs, results, and intermediate artifacts

Constraint: Must verify directories exist and are writable.
"""
import os
import sys
import argparse
from pathlib import Path
from typing import List, Tuple

def get_project_root() -> Path:
    """
    Determine the project root directory.
    Assumes the script is run from the project root or a subdirectory of it.
    """
    current = Path.cwd()
    # Look for a marker file or just assume the current directory is the root
    # given the task context (PROJ-884-llmxive-follow-up-extending-self-improvi)
    if (current / "tasks.md").exists():
        return current
    # Fallback: traverse up until we find tasks.md or hit the filesystem root
    while current != current.parent:
        if (current / "tasks.md").exists():
            return current
        current = current.parent
    # If not found, assume current working directory
    return Path.cwd()

def setup_data_directories(project_root: Path) -> Tuple[bool, List[str]]:
    """
    Create the required data directory structure and verify writability.
    
    Creates:
    - data/raw
    - data/processed
    
    Returns:
        Tuple[success: bool, messages: List[str]]
    """
    data_root = project_root / "data"
    raw_dir = data_root / "raw"
    processed_dir = data_root / "processed"
    
    messages = []
    success = True

    # Ensure data root exists
    if not data_root.exists():
        try:
            data_root.mkdir(parents=True, exist_ok=True)
            messages.append(f"Created data root: {data_root}")
        except OSError as e:
            messages.append(f"ERROR: Failed to create data root {data_root}: {e}")
            success = False
            return success, messages

    # Create and verify data/raw
    if not raw_dir.exists():
        try:
            raw_dir.mkdir(parents=True, exist_ok=True)
            messages.append(f"Created data/raw: {raw_dir}")
        except OSError as e:
            messages.append(f"ERROR: Failed to create data/raw {raw_dir}: {e}")
            success = False

    # Verify data/raw is writable
    if raw_dir.exists():
        test_file = raw_dir / ".write_test"
        try:
            with open(test_file, 'w') as f:
                f.write("write_test")
            if test_file.exists():
                test_file.unlink() # Clean up
                messages.append(f"Verified writability: {raw_dir}")
            else:
                messages.append(f"ERROR: Could not verify writability of {raw_dir} (file disappeared?)")
                success = False
        except OSError as e:
            messages.append(f"ERROR: data/raw is not writable: {e}")
            success = False

    # Create and verify data/processed
    if not processed_dir.exists():
        try:
            processed_dir.mkdir(parents=True, exist_ok=True)
            messages.append(f"Created data/processed: {processed_dir}")
        except OSError as e:
            messages.append(f"ERROR: Failed to create data/processed {processed_dir}: {e}")
            success = False

    # Verify data/processed is writable
    if processed_dir.exists():
        test_file = processed_dir / ".write_test"
        try:
            with open(test_file, 'w') as f:
                f.write("write_test")
            if test_file.exists():
                test_file.unlink() # Clean up
                messages.append(f"Verified writability: {processed_dir}")
            else:
                messages.append(f"ERROR: Could not verify writability of {processed_dir} (file disappeared?)")
                success = False
        except OSError as e:
            messages.append(f"ERROR: data/processed is not writable: {e}")
            success = False

    return success, messages

def main():
    """
    CLI entry point for T004.
    """
    parser = argparse.ArgumentParser(
        description="Setup data directory structure (T004)."
    )
    parser.add_argument(
        "--project-root",
        type=str,
        default=None,
        help="Path to the project root. If not provided, auto-detected."
    )
    
    args = parser.parse_args()
    
    project_root = Path(args.project_root) if args.project_root else get_project_root()
    
    print(f"Project root detected: {project_root}")
    print("-" * 40)
    
    success, messages = setup_data_directories(project_root)
    
    for msg in messages:
        print(msg)
    
    print("-" * 40)
    if success:
        print("SUCCESS: Data directory structure setup and verified.")
        sys.exit(0)
    else:
        print("FAILURE: Data directory setup encountered errors.")
        sys.exit(1)

if __name__ == "__main__":
    main()
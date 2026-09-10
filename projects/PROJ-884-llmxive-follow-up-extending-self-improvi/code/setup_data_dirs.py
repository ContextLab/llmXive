import os
import sys
import argparse
from pathlib import Path
from typing import List, Tuple

def setup_data_directories(base_path: Path) -> List[Tuple[Path, bool]]:
    """
    Create the data directory structure:
    - data/raw (for immutable puzzles)
    - data/processed (for logs/results)
    
    Returns a list of (path, success) tuples for verification.
    """
    data_root = base_path / "data"
    raw_dir = data_root / "raw"
    processed_dir = data_root / "processed"
    
    directories = [
        (data_root, "Data root"),
        (raw_dir, "Raw data"),
        (processed_dir, "Processed data"),
    ]
    
    results = []
    
    for dir_path, desc in directories:
        try:
            # Create directory if it doesn't exist
            dir_path.mkdir(parents=True, exist_ok=True)
            
            # Verify it exists and is writable
            if not dir_path.exists():
                results.append((dir_path, False))
                print(f"ERROR: Failed to create {desc} directory: {dir_path}")
                continue
            
            # Test writability by creating a temporary file
            test_file = dir_path / ".write_test"
            try:
                test_file.touch()
                test_file.unlink()
                results.append((dir_path, True))
                print(f"SUCCESS: {desc} directory created and verified writable: {dir_path}")
            except (PermissionError, OSError) as e:
                results.append((dir_path, False))
                print(f"ERROR: {desc} directory not writable: {dir_path} - {e}")
                
        except Exception as e:
            results.append((dir_path, False))
            print(f"ERROR: Failed to create {desc} directory: {dir_path} - {e}")
    
    return results

def main():
    """
    CLI entry point for setting up data directories.
    """
    parser = argparse.ArgumentParser(
        description="Setup data directory structure for llmXive project"
    )
    parser.add_argument(
        "--base-path",
        type=Path,
        default=Path("."),
        help="Base path for the project (default: current directory)"
    )
    
    args = parser.parse_args()
    
    print(f"Setting up data directories in: {args.base_path}")
    print("-" * 60)
    
    results = setup_data_directories(args.base_path)
    
    print("-" * 60)
    all_success = all(success for _, success in results)
    
    if all_success:
        print("All data directories created and verified successfully.")
        sys.exit(0)
    else:
        failed_dirs = [str(path) for path, success in results if not success]
        print(f"ERROR: Failed to create/verify directories: {failed_dirs}")
        sys.exit(1)

if __name__ == "__main__":
    main()

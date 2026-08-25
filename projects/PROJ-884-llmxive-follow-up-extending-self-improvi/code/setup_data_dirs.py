"""
Script to setup the data directory hierarchy for the llmXive project.
Creates data/raw and data/processed directories and verifies they are writable.
"""
import os
import sys
import argparse
from pathlib import Path
from typing import List

def setup_data_directories(base_dir: Path) -> List[Path]:
    """
    Create the required data directory structure.
    
    Args:
        base_dir: The root directory of the project.
        
    Returns:
        List of created directory paths.
        
    Raises:
        RuntimeError: If a directory cannot be created or is not writable.
    """
    data_dir = base_dir / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    
    directories = [data_dir, raw_dir, processed_dir]
    
    for directory in directories:
        # Create directory if it doesn't exist
        if not directory.exists():
            try:
                directory.mkdir(parents=True, exist_ok=True)
                print(f"Created directory: {directory}")
            except OSError as e:
                raise RuntimeError(f"Failed to create directory {directory}: {e}")
        
        # Verify the directory is writable
        if not os.access(directory, os.W_OK):
            raise RuntimeError(f"Directory {directory} exists but is not writable.")
        
        # Verify we can create a temporary file to ensure writability
        test_file = directory / ".write_test"
        try:
            with open(test_file, 'w') as f:
                f.write("test")
            test_file.unlink()
        except OSError as e:
            raise RuntimeError(f"Cannot write to directory {directory}: {e}")
    
    return directories

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Setup data directory hierarchy for llmXive project."
    )
    parser.add_argument(
        "--base-dir",
        type=str,
        default=".",
        help="Base directory for the project (default: current directory)"
    )
    
    args = parser.parse_args()
    base_dir = Path(args.base_dir).resolve()
    
    print(f"Setting up data directories in: {base_dir}")
    
    try:
        created_dirs = setup_data_directories(base_dir)
        print("Data directory setup completed successfully.")
        print("Created directories:")
        for d in created_dirs:
            print(f"  - {d}")
        
        # Verify final state
        data_dir = base_dir / "data"
        raw_dir = data_dir / "raw"
        processed_dir = data_dir / "processed"
        
        assert data_dir.exists(), "data directory missing"
        assert raw_dir.exists(), "data/raw directory missing"
        assert processed_dir.exists(), "data/processed directory missing"
        
        print("Verification passed: All required directories exist and are writable.")
        return 0
        
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())

import os
import sys
from pathlib import Path

def main():
    """
    Creates the 'data/filtered' directory if it does not exist.
    This script is part of the T001i task implementation.
    """
    project_root = Path(__file__).resolve().parent.parent
    filtered_dir = project_root / "data" / "filtered"

    if not filtered_dir.exists():
        filtered_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {filtered_dir}")
    else:
        print(f"Directory already exists: {filtered_dir}")
    
    # Ensure the directory is writable (optional check)
    try:
        test_file = filtered_dir / ".gitkeep"
        test_file.touch()
        test_file.unlink()
        print(f"Verified write access to: {filtered_dir}")
    except OSError as e:
        print(f"Warning: Could not verify write access to {filtered_dir}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
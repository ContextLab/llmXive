"""
Script to setup the raw data directory structure for GSM8K and LogiQA.
This task creates empty directories to ensure the data pipeline has
the correct folder structure before data download or processing.
"""
import os
import sys
from pathlib import Path

# Ensure the script can import from the project root if run directly
# or from the code/data package if run as a module
def ensure_dir(path: Path) -> None:
    """Create directory if it does not exist."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
    elif not path.is_dir():
        raise RuntimeError(f"Path exists but is not a directory: {path}")

def main() -> None:
    """Create the required raw data directories."""
    # Determine project root relative to this file
    # Assuming this file is at code/data/setup_directories.py
    project_root = Path(__file__).resolve().parent.parent.parent
    
    data_raw_dir = project_root / "data" / "raw"
    gsm8k_dir = data_raw_dir / "gsm8k"
    logiqa_dir = data_raw_dir / "logiqa"

    print(f"Project root detected at: {project_root}")
    print(f"Creating directory structure under: {data_raw_dir}")

    try:
        ensure_dir(data_raw_dir)
        ensure_dir(gsm8k_dir)
        ensure_dir(logiqa_dir)
        
        # Verify creation
        assert gsm8k_dir.is_dir(), "GSM8K directory creation failed"
        assert logiqa_dir.is_dir(), "LogiQA directory creation failed"
        
        print(f"Successfully created: {gsm8k_dir}")
        print(f"Successfully created: {logiqa_dir}")
        print("Directory structure setup complete.")
        
    except Exception as e:
        print(f"Error setting up directories: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
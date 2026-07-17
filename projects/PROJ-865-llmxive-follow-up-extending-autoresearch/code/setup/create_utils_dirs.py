import os
import sys
from pathlib import Path

def main():
    """Create the code/utils/ directory structure."""
    root = Path(__file__).resolve().parent.parent.parent
    utils_dir = root / "code" / "utils"
    
    if not utils_dir.exists():
        utils_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {utils_dir}")
    else:
        print(f"Directory already exists: {utils_dir}")

if __name__ == "__main__":
    main()
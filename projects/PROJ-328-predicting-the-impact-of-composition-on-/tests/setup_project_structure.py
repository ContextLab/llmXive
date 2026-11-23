import os
import sys
from pathlib import Path

def main():
    """
    Simple verification script to ensure the directory structure is correct.
    This is a lightweight check to be run after setup.
    """
    base_dir = Path(__file__).resolve().parent.parent
    required_dirs = [
        "code",
        "code/ingestion",
        "code/features",
        "code/models",
        "code/evaluation",
        "code/visualization",
        "code/utils",
        "tests",
        "tests/contract",
        "tests/integration",
    ]

    missing = []
    for rel_path in required_dirs:
        full_path = base_dir / rel_path
        if not full_path.exists():
            missing.append(rel_path)
        elif not full_path.is_dir():
            missing.append(rel_path)

    if missing:
        print(f"ERROR: Missing directories: {missing}")
        return 1
    
    print("SUCCESS: All required directories exist.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
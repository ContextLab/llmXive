import os
import sys
from pathlib import Path

# Project root is the parent of the 'tools' directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

REQUIRED_DIRS = [
    "projects/PROJ-068-evaluating-the-performance-of-different-/code",
    "projects/PROJ-068-evaluating-the-performance-of-different-/tests",
    "projects/PROJ-068-evaluating-the-performance-of-different-/data",
    "projects/PROJ-068-evaluating-the-performance-of-different-/results",
]

def main():
    """Verify that all required project directories exist."""
    print(f"Verifying project structure at: {PROJECT_ROOT}")
    
    missing_dirs = []
    for dir_path in REQUIRED_DIRS:
        full_path = PROJECT_ROOT / dir_path
        if not full_path.exists():
            missing_dirs.append(dir_path)
        else:
            print(f"[OK] {dir_path}")
    
    if missing_dirs:
        print("\n[FAIL] Missing directories:")
        for d in missing_dirs:
            print(f"  - {d}")
        sys.exit(1)
    
    print("\n[SUCCESS] All required directories exist.")
    sys.exit(0)

if __name__ == "__main__":
    main()
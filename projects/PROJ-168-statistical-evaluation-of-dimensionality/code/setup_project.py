import os
import sys
from pathlib import Path

def main():
    """
    Creates the project directory structure for the statistical evaluation of dimensionality reduction.
    Implements T001: mkdir -p projects/001-statistical-evaluation-of-dimensionality/{data/raw,data/processed,results,code,tests}
    """
    project_root = Path("projects/001-statistical-evaluation-of-dimensionality")
    
    # Define the required subdirectories
    directories = [
        "data/raw",
        "data/processed",
        "results",
        "code",
        "tests"
    ]
    
    created_dirs = []
    for d in directories:
        dir_path = project_root / d
        dir_path.mkdir(parents=True, exist_ok=True)
        created_dirs.append(str(dir_path))
        print(f"Created directory: {dir_path}")
    
    # Verify structure
    print(f"\nProject structure initialized at: {project_root}")
    print("Verification of created directories:")
    for d in created_dirs:
        if os.path.isdir(d):
            print(f"  [OK] {d}")
        else:
            print(f"  [FAIL] {d}")
            return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

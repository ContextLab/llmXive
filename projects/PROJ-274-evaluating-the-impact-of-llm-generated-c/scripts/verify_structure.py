import os
import sys
from pathlib import Path

def main():
    # Define the project root based on the task description
    # The script is in scripts/, so we look up one level for the project root
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent
    
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/reports",
        "code",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "specs"
    ]

    missing = []
    for rel_path in required_dirs:
        full_path = project_root / rel_path
        if not full_path.is_dir():
            missing.append(str(full_path))
    
    if missing:
        print(f"ERROR: The following required directories are missing:")
        for m in missing:
            print(f"  - {m}")
        sys.exit(1)
    
    print("SUCCESS: All required project directories exist.")
    sys.exit(0)

if __name__ == "__main__":
    main()
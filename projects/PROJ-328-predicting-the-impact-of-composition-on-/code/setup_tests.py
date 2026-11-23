import os
import sys
from pathlib import Path

def main():
    """
    Main entry point for test setup.
    Ensures test directories are properly initialized.
    """
    project_root = Path(__file__).resolve().parent.parent
    
    test_dirs = [
        "tests/contract",
        "tests/integration",
        "tests/unit",
    ]
    
    for dir_path in test_dirs:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Ensured test directory: {full_path}")
    
    print("Test setup complete")
    return 0

if __name__ == "__main__":
    sys.exit(main())

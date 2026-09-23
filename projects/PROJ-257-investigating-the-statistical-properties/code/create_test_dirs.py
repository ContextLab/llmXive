import os
import sys
from pathlib import Path

def create_directories():
    """Create the root-level test directories."""
    test_dirs = [
        "tests/unit",
        "tests/integration",
        "tests/contract"
    ]
    
    for dir_path in test_dirs:
        full_path = Path(dir_path)
        full_path.mkdir(parents=True, exist_ok=True)
        # Create .gitkeep to ensure directories are tracked by git
        gitkeep_path = full_path / ".gitkeep"
        gitkeep_path.touch(exist_ok=True)
        
    # Also create a root .gitkeep for tests/ if it doesn't exist
    root_tests = Path("tests")
    root_tests.mkdir(parents=True, exist_ok=True)
    (root_tests / ".gitkeep").touch(exist_ok=True)
        
    print(f"Created {len(test_dirs)} test subdirectories with .gitkeep files.")

def main():
    create_directories()
    print("Test directory initialization complete.")

if __name__ == "__main__":
    main()

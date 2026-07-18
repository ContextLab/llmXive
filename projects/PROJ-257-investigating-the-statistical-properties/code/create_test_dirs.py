import os
import sys
from pathlib import Path

def create_directories(root_path: str = ".") -> None:
    """
    Create the tests directory structure at the repository root.
    
    Creates:
      - tests/
      - tests/unit/
      - tests/integration/
      - tests/contract/
      - tests/.gitkeep
    
    Args:
        root_path: Base path for the project (defaults to current directory).
    """
    base = Path(root_path)
    tests_dir = base / "tests"
    
    # Define subdirectories required by T001b
    subdirs = ["unit", "integration", "contract"]
    
    # Create main tests directory
    tests_dir.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories
    for subdir in subdirs:
        (tests_dir / subdir).mkdir(parents=True, exist_ok=True)
    
    # Create .gitkeep to ensure directory is tracked by git
    gitkeep_path = tests_dir / ".gitkeep"
    gitkeep_path.touch()
    
    print(f"Created directory structure under {tests_dir}")
    for subdir in subdirs:
        print(f"  - tests/{subdir}/")
    print(f"  - tests/.gitkeep")

def main() -> None:
    """Entry point for directory creation script."""
    create_directories(".")

if __name__ == "__main__":
    main()
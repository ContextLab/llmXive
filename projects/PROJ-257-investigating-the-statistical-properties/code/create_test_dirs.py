import os
import sys
from pathlib import Path

def create_directories():
    """
    Create the tests/ directory structure at the repository root.
    Creates:
      - tests/
      - tests/.gitkeep
      - tests/unit/
      - tests/integration/
      - tests/contract/
    """
    root = Path(__file__).resolve().parent.parent
    tests_dir = root / "tests"
    
    # Create main tests directory
    tests_dir.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories
    (tests_dir / "unit").mkdir(exist_ok=True)
    (tests_dir / "integration").mkdir(exist_ok=True)
    (tests_dir / "contract").mkdir(exist_ok=True)
    
    # Create .gitkeep files to ensure directories are tracked by git
    (tests_dir / ".gitkeep").touch()
    (tests_dir / "unit" / ".gitkeep").touch()
    (tests_dir / "integration" / ".gitkeep").touch()
    (tests_dir / "contract" / ".gitkeep").touch()
    
    print(f"Created directory structure under: {tests_dir}")
    return True

def main():
    """Entry point for script execution."""
    success = create_directories()
    if success:
        print("Task T001c/T001d setup complete.")
        sys.exit(0)
    else:
        print("Failed to create test directories.")
        sys.exit(1)

if __name__ == "__main__":
    main()

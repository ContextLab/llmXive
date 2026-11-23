import os
import sys
from pathlib import Path

def ensure_directory(path: str) -> None:
    """Create directory and a .gitkeep file if it doesn't exist."""
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    gitkeep = dir_path / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.touch()

def main():
    """Initialize project directory structure."""
    # Directories to create based on task T003
    directories = [
        "explanations",
        "state",
        "tests",
        # Ensure subdirectories for tests as well
        "tests/contract",
        "tests/integration",
        "tests/unit",
    ]

    for dir_path in directories:
        ensure_directory(dir_path)
        print(f"Created: {dir_path}/")

    # Verify existence
    print("\nVerification:")
    for dir_path in directories:
        p = Path(dir_path)
        if p.exists():
            print(f"  [OK] {dir_path}/ exists")
        else:
            print(f"  [FAIL] {dir_path}/ missing")
            sys.exit(1)

if __name__ == "__main__":
    main()

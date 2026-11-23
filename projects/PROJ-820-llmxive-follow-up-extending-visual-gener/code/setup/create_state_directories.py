import os
import sys
from pathlib import Path

def create_directory(path: Path) -> None:
    """Create a directory if it does not exist."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")
    else:
        print(f"Directory already exists: {path}")

def main() -> None:
    """
    Specific helper for state directories if needed.
    """
    project_root = Path.cwd()
    state_dirs = [
        project_root / "state" / "projects",
    ]
    for d in state_dirs:
        create_directory(d)

if __name__ == "__main__":
    main()

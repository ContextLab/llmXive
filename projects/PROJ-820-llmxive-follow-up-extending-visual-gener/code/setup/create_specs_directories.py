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
    Specific helper for specs directories if needed, 
    though create_directories covers all. Kept for API surface compatibility.
    """
    project_root = Path.cwd()
    specs_dirs = [
        project_root / "specs" / "001-llmxive-followup",
        project_root / "specs" / "001-llmxive-followup" / "contracts",
    ]
    for d in specs_dirs:
        create_directory(d)

if __name__ == "__main__":
    main()

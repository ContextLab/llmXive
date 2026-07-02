import os
import sys
from pathlib import Path

def create_directories(base_path: Path) -> None:
    """
    Ensure specific data directories exist with .gitkeep files.
    This is a specialized helper for data directory initialization.
    """
    data_dirs = [
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "data" / "external",
    ]

    for dir_path in data_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        gitkeep = dir_path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.write_text("")
        print(f"Ensured directory: {dir_path}")

def main():
    """Main entry point."""
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    create_directories(project_root)
    print("Data directories ensured.")

if __name__ == "__main__":
    main()
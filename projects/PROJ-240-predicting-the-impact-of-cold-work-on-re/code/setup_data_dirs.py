import os
from pathlib import Path

def main():
    """
    Create data subdirectories: data/raw, data/processed, data/split.
    Create .gitkeep files in all new directories to ensure they are tracked by version control.
    """
    # Determine project root relative to this script's location
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    data_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "split",
    ]

    for dir_path in data_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        gitkeep_path = dir_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
        print(f"Ensured directory exists: {dir_path}")
        print(f"Ensured .gitkeep exists: {gitkeep_path}")

    print("Data subdirectories setup complete.")

if __name__ == "__main__":
    main()

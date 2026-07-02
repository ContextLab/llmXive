import os
from pathlib import Path

def create_data_directories(base_path: Path) -> None:
    """Create data subdirectories."""
    data_dirs = [
        "data/raw-fmri",
        "data/processed-fmri",
        "data/behavioral",
        "data/results",
    ]

    for dir_path in data_dirs:
        full_path = base_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        # Create .gitkeep to ensure directories are tracked by git
        gitkeep = full_path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.write_text("# Placeholder for data files\n")

def main():
    """Main entry point for setting up data directories."""
    base_path = Path.cwd()
    create_data_directories(base_path)
    print("Data directories created successfully.")

if __name__ == "__main__":
    main()
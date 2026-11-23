"""
Script to initialize the data directory structure for the project.
Creates raw/, processed/, and contracts/ subdirectories under data/.
"""
import os
from pathlib import Path

def ensure_dir(path: Path) -> None:
    """Create directory if it does not exist."""
    os.makedirs(path, exist_ok=True)
    # Create .gitkeep to ensure directories are tracked in git
    gitkeep_path = path / ".gitkeep"
    if not gitkeep_path.exists():
        gitkeep_path.touch()

def main() -> None:
    """Create the data directory structure."""
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data"

    # Define subdirectories
    subdirs = ["raw", "processed", "contracts"]

    # Ensure base data directory exists
    ensure_dir(data_dir)

    # Create subdirectories
    for subdir in subdirs:
        ensure_dir(data_dir / subdir)

    print(f"Data directory structure created at: {data_dir}")
    for subdir in subdirs:
        print(f"  - {data_dir / subdir}/")

if __name__ == "__main__":
    main()

import sys
from pathlib import Path
from typing import List

def _project_root() -> Path:
    """
    Return the absolute path to the repository root.
    This script is located at <root>/code/setup_project_structure.py.
    """
    return Path(__file__).resolve().parent.parent

def _required_directories(root: Path) -> List[Path]:
    """
    Define the required directory layout for the research pipeline as per T001.
    """
    return [
        root / "src",
        root / "src/utils",
        root / "data/raw",
        root / "data/derived",
        root / "data/annotations",
        root / "results",
        root / "tests",
        root / "specs",
        root / "contracts",
        root / "logs",
    ]

def create_directories() -> List[Path]:
    """
    Create all required directories if they do not already exist.
    """
    root = _project_root()
    dirs = _required_directories(root)
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    return dirs

def main() -> int:
    """
    Entry point for creating and verifying the directory layout.
    Asserts that each directory exists after creation.
    """
    try:
        dirs = create_directories()
        print("Verifying directory layout...")
        for d in dirs:
            if not d.is_dir():
                print(f"Verification Failed: {d} is not a directory.")
                return 1
            print(f"Verified: {d}")
        print("Project structure verified successfully.")
        return 0
    except Exception as e:
        print(f"Unexpected error during directory setup: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
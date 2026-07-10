import os
from pathlib import Path
from typing import Final

_PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent

def get_project_root() -> Path:
    """Get the project root directory."""
    return _PROJECT_ROOT

def ensure_directories() -> None:
    """Ensure all required directories exist."""
    root = get_project_root()
    dirs = [
        root / "data" / "raw" / "stimuli",
        root / "data" / "raw" / "responses",
        root / "data" / "processed",
        root / "data" / "results",
        root / "logs",
        root / "figures"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def get_data_path() -> Path:
    """Get the path to the data directory."""
    return get_project_root() / "data"

if __name__ == "__main__":
    print(f"Project root: {get_project_root()}")
    ensure_directories()
    print("Directories ensured.")

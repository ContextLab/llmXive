import os
from pathlib import Path
from typing import Final

# Project constants
PROJECT_NAME: Final[str] = "PROJ-026-the-influence-of-visual-complexity-on-im"
SEED: Final[int] = 42

# Root directories
_PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent

CODE_ROOT: Final[Path] = _PROJECT_ROOT / "code"
DATA_ROOT: Final[Path] = _PROJECT_ROOT / "data"
RESULTS_ROOT: Final[Path] = _PROJECT_ROOT / "data" / "results"
DOCS_ROOT: Final[Path] = _PROJECT_ROOT / "docs"


def get_project_root() -> Path:
    """Get the project root directory."""
    return _PROJECT_ROOT


def ensure_directories() -> None:
    """Ensure all required directories exist."""
    dirs = [
        CODE_ROOT / "data",
        CODE_ROOT / "stimuli",
        CODE_ROOT / "analysis",
        CODE_ROOT / "viz",
        CODE_ROOT / "tests",
        DATA_ROOT / "raw" / "stimuli",
        DATA_ROOT / "raw" / "responses",
        DATA_ROOT / "processed",
        DATA_ROOT / "results",
        DOCS_ROOT,
        CODE_ROOT / "logs"
    ]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def get_data_path(subpath: str) -> Path:
    """Get a path relative to the data root."""
    return DATA_ROOT / subpath


if __name__ == "__main__":
    print(f"Project root: {get_project_root()}")
    ensure_directories()
    print("Directories ensured.")

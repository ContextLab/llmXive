"""
Project‑setup helper used by the CI to create the required folder hierarchy.
Updated to also create ``docs/reports`` so that the directory exists before
any script attempts to write report files.
"""
import os
from pathlib import Path

def get_project_root() -> Path:
    """Return the root directory of the repository (parent of ``code``)."""
    return Path(__file__).resolve().parent.parent

def create_directories(project_root: Path) -> None:
    """Create all mandatory directories for the pipeline."""
    dirs = [
        project_root / "code" / "src",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "docs" / "reports",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def create_gitkeep(project_root: Path) -> None:
    """Create ``.gitkeep`` files so empty directories are tracked by git."""
    for root, _, files in os.walk(project_root):
        if not files:
            (Path(root) / ".gitkeep").touch()

def main() -> None:
    """Entry point for project setup."""
    root = get_project_root()
    create_directories(root)
    create_gitkeep(root)

if __name__ == "__main__":
    main()
"""T001: Create the project directory structure.

Creates (idempotently):
  data/raw
  data/processed
  code
  tests/unit
  state/projects

Run from anywhere; paths are resolved relative to this file's location
(projects/PROJ-826-llmxive-follow-up-extending-memlens-benc/).
"""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DIRECTORIES = [
    PROJECT_ROOT / "data" / "raw",
    PROJECT_ROOT / "data" / "processed",
    PROJECT_ROOT / "code",
    PROJECT_ROOT / "tests" / "unit",
    PROJECT_ROOT / "state" / "projects",
]


def create_directories() -> None:
    for directory in DIRECTORIES:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"[T001] ensured directory: {directory.relative_to(PROJECT_ROOT)}")
    # Verify existence (fail loudly if anything is missing).
    missing = [d for d in DIRECTORIES if not d.is_dir()]
    if missing:
        raise RuntimeError(f"Failed to create directories: {missing}")
    print("[T001] all directories verified present.")


if __name__ == "__main__":
    create_directories()
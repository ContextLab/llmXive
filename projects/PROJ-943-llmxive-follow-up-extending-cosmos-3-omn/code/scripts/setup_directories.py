"""T001: Create standard project directories with .gitkeep files.

Creates the directory structure required by the project plan:
code/scripts, code/data/raw, code/data/processed, code/data/splits,
code/models, code/tests, code/reports, code/utils
Each directory receives a .gitkeep file (with a short comment so it is
non-empty) for version-control persistence.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CODE_DIR = PROJECT_ROOT / "code"

DIRECTORIES = [
    "scripts",
    "data/raw",
    "data/processed",
    "data/splits",
    "models",
    "tests",
    "reports",
    "utils",
]

GITKEEP_CONTENT = (
    "# This file ensures the directory is tracked by version control.\n"
)


def create_directory(base_path: Path, dir_name: str) -> bool:
    """Create a directory and its .gitkeep file if it doesn't exist."""
    target = base_path / dir_name
    target.mkdir(parents=True, exist_ok=True)
    gitkeep = target / ".gitkeep"
    if not gitkeep.exists() or gitkeep.stat().st_size == 0:
        gitkeep.write_text(GITKEEP_CONTENT, encoding="utf-8")
    return gitkeep.exists() and gitkeep.stat().st_size > 0


def main() -> int:
    if not CODE_DIR.is_dir():
        print(f"ERROR: expected code directory at {CODE_DIR}", file=sys.stderr)
        return 1
    all_ok = True
    for dir_name in DIRECTORIES:
        ok = create_directory(CODE_DIR, dir_name)
        status = "OK" if ok else "FAILED"
        print(f"[{status}] {CODE_DIR / dir_name} (.gitkeep present)")
        all_ok = all_ok and ok
    if not all_ok:
        print("ERROR: some directories or .gitkeep files failed", file=sys.stderr)
        return 1
    print("All project directories and .gitkeep files are in place.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
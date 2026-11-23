"""
Project structure setup (T001).

Creates the standard project directory tree per the implementation plan:
    code/  data/raw/  data/processed/  results/  logs/  figures/

Adds .gitkeep files so empty directories are preserved in version control.
Idempotent: safe to run repeatedly.
"""
import sys
from pathlib import Path

# Directories required by the implementation plan / tasks.md T001
REQUIRED_DIRS = [
    "code",
    "data/raw",
    "data/processed",
    "results",
    "logs",
    "figures",
]

# Directories that should carry a .gitkeep placeholder when empty
GITKEEP_DIRS = [
    "data/raw",
    "data/processed",
    "results",
    "logs",
]


def create_project_structure(root: Path = None) -> None:
    """Create the required project directory tree under `root`."""
    base = Path(root) if root is not None else Path.cwd()

    created = []
    for d in REQUIRED_DIRS:
        path = base / d
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created.append(str(path))
        elif not path.is_dir():
            raise NotADirectoryError(
                f"Expected a directory but found a file: {path}"
              )

    for d in GITKEEP_DIRS:
        keep = base / d / ".gitkeep"
        if not keep.exists():
            keep.touch()

    # Report
    if created:
        print("Created directories:")
        for c in created:
            print(f"  {c}")
    else:
        print("All required directories already exist.")
    print("Project structure verified:")
    for d in REQUIRED_DIRS:
        print(f"  {base / d} -> exists={ (base / d).is_dir() }")

    # Verify all required dirs exist; fail loudly otherwise
    missing = [d for d in REQUIRED_DIRS if not (base / d).is_dir()]
    if missing:
        raise RuntimeError(f"Failed to create directories: {missing}")


def main() -> int:
    create_project_structure()
    return 0


if __name__ == "__main__":
    sys.exit(main())
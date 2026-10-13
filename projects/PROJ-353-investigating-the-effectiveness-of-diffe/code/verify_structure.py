"""
Verification script for required project directory layout.

When executed as a module (python -m code.verify_structure) it checks that all
directories required by the project exist relative to the repository root.
It exits with code 0 if everything is present, otherwise prints the missing
paths and exits with code 1.
"""
import sys
from pathlib import Path

# List of directories (relative to the repository root) that must exist.
REQUIRED_DIRS = [
    "code",
    "tests",
    "data",
    "data/raw",
    "data/processed",
    "data/analysis",
    "artifacts",
    "contracts",
]


def _project_root() -> Path:
    """
    Resolve the repository root directory.

    The script lives in <root>/code/verify_structure.py, so the root is two
    levels up from this file.
    """
    return Path(__file__).resolve().parent.parent


def main() -> None:
    root = _project_root()
    missing = []

    for rel_path in REQUIRED_DIRS:
        dir_path = root / rel_path
        if not dir_path.is_dir():
            missing.append(str(dir_path))

    if missing:
        print("Missing required directories:")
        for p in missing:
            print(p)
        sys.exit(1)

    # All required directories are present.
    sys.exit(0)


if __name__ == "__main__":
    main()

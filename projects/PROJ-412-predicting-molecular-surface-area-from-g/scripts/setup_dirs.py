"""Setup script for code-related directory structure (T001-Setup-Dirs-Code).

Creates the required project directories:
code/, code/data/, code/models/, code/eval/, code/utils/,
tests/contract/, tests/unit/, tests/integration/, logs/

Run from the repository root:
    python scripts/setup_dirs.py
"""

import sys
from pathlib import Path

CODE_DIRS = [
    "code",
    "code/data",
    "code/models",
    "code/eval",
    "code/utils",
    "tests/contract",
    "tests/unit",
    "tests/integration",
    "logs",
]


def create_directories(base: Path = None) -> list:
    """Create all code-related directories under the given base path.

    Args:
        base: Base path (defaults to repository root, i.e. parent of scripts/).

    Returns:
        List of Path objects for the created directories.
    """
    if base is None:
        base = Path(__file__).resolve().parent.parent
    created = []
    for rel in CODE_DIRS:
        d = base / rel
        d.mkdir(parents=True, exist_ok=True)
        created.append(d)
    return created


def verify_directories(base: Path = None) -> bool:
    """Verify that all required directories exist.

    Returns:
        True if all directories exist, False otherwise.
    """
    if base is None:
        base = Path(__file__).resolve().parent.parent
    return all((base / rel).is_dir() for rel in CODE_DIRS)


def main() -> int:
    created = create_directories()
    for d in created:
        print(f"OK: {d}")
    if verify_directories():
        print("All code-related directories created and verified.")
        return 0
    print("ERROR: directory verification failed.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
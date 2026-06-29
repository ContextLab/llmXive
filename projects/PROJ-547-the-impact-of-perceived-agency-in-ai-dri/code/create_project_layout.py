"""Create and verify the standard project directory layout.

This script ensures that the following top‑level directories exist:
- code/
- tests/
- data/
- configs/
- logs/
- docs/

It also creates empty ``__init__.py`` files in ``code/`` and ``tests/`` so that
they are recognised as Python packages.

Running the script is idempotent – existing directories or files are left
untouched.
"""

import sys
from pathlib import Path

def create_directories(base_path: Path, dirs: list[str]) -> None:
    """Create each directory under ``base_path`` if it does not already exist."""
    for d in dirs:
        dir_path = base_path / d
        dir_path.mkdir(parents=True, exist_ok=True)

def ensure_init_file(pkg_path: Path) -> None:
    """Create an empty ``__init__.py`` file inside ``pkg_path`` if missing."""
    init_file = pkg_path / "__init__.py"
    if not init_file.exists():
        init_file.touch()

def verify_layout(base_path: Path, dirs: list[str]) -> None:
    """Raise ``RuntimeError`` if any required element is missing."""
    missing = []
    for d in dirs:
        dir_path = base_path / d
        if not dir_path.is_dir():
            missing.append(f"Directory missing: {dir_path}")
    for pkg in ("code", "tests"):
        init_path = base_path / pkg / "__init__.py"
        if not init_path.is_file():
            missing.append(f"Missing __init__.py in {base_path / pkg}")
    if missing:
        raise RuntimeError("\n".join(missing))

def main() -> int:
    project_root = Path(__file__).resolve().parent.parent  # repository root
    required_dirs = ["code", "tests", "data", "configs", "logs", "docs"]

    # Step 1: create directories
    create_directories(project_root, required_dirs)

    # Step 2: create package markers
    ensure_init_file(project_root / "code")
    ensure_init_file(project_root / "tests")

    # Step 3: verification
    try:
        verify_layout(project_root, required_dirs)
    except RuntimeError as exc:
        print(f"Project layout verification failed:\n{exc}", file=sys.stderr)
        return 1

    print("Project layout created and verified successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())

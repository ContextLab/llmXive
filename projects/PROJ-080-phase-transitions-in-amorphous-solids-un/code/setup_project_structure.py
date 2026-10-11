"""Setup project directory hierarchy for the Phase Transitions in Amorphous Solids pipeline.

This script creates the following directories relative to the project root
(the directory that contains the ``code`` folder):

- data/raw
- data/processed
- code               (ensured to exist)
- tests/unit
- tests/integration
- specs/contracts

The script can be invoked without arguments; it will infer the project
root as the parent directory of this script's ``code`` folder. An optional
``--project-root`` flag allows overriding the inferred location.
"""

import argparse
import sys
from pathlib import Path


def _create_directories(root: Path) -> None:
    """Create the required directory tree under *root*."""
    dirs = [
        root / "data" / "raw",
        root / "data" / "processed",
        root / "code",
        root / "tests" / "unit",
        root / "tests" / "integration",
        root / "specs" / "contracts",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create the directory hierarchy required for the pipeline."
    )
    parser.add_argument(
        "--project-root",
        type=str,
        default=None,
        help=(
            "Path to the project root. If omitted, the script infers the root as the "
            "parent directory of this script's ``code`` folder."
        ),
    )
    args = parser.parse_args()

    # Determine the root directory
    if args.project_root:
        project_root = Path(args.project_root).expanduser().resolve()
    else:
        # ``__file__`` points to ``.../code/setup_project_structure.py``
        # Its parent is ``code``; the project root is one level up.
        project_root = Path(__file__).resolve().parent.parent

    try:
        _create_directories(project_root)
        print(f"Project directories created under: {project_root}")
    except Exception as exc:  # pragma: no cover – unexpected I/O errors
        print(f"Failed to create directories: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
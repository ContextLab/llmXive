"""Setup project directory hierarchy for the Phase Transitions in Amorphous Solids pipeline.

This script creates the following directories relative to the repository root,
specifically under the project folder
``projects/PROJ-080-phase-transitions-in-amorphous-solids-un``:

- data/raw
- data/processed
- code
- tests/unit
- tests/integration
- specs/contracts

The script can be invoked without arguments; it will infer the project
root as ``projects/PROJ-080-phase-transitions-in-amorphous-solids-un``.
An optional ``--project-root`` flag allows overriding the inferred location.
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
            "Path to the project root. If omitted, defaults to "
            "projects/PROJ-080-phase-transitions-in-amorphous-solids-un "
            "relative to the repository root."
        ),
    )
    args = parser.parse_args()

    # Determine the root directory
    if args.project_root:
        project_root = Path(args.project_root).expanduser().resolve()
    else:
        # Repository root is the parent of the ``code`` folder containing this script
        repo_root = Path(__file__).resolve().parent.parent
        project_root = repo_root / "projects" / "PROJ-080-phase-transitions-in-amorphous-solids-un"

    try:
        _create_directories(project_root)
        print(f"Project directories created under: {project_root}")
    except Exception as exc:  # pragma: no cover – unexpected I/O errors
        print(f"Failed to create directories: {exc}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
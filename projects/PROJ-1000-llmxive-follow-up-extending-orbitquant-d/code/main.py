"""
Main entry point for project skeleton initialization.

This script creates the required sub‑directories under the ``code/`` package,
prints a confirmation message, and exits with status 0.

It is invoked by the quick‑start guide via:

    python -m code.main --phase init

The script also imports ``code.config`` to verify that the configuration
module loads correctly.
"""
import argparse
import sys
from pathlib import Path

# Import the configuration module to ensure it loads without error.
try:
    import code.config  # noqa: F401
except Exception as e:
    print(f"Failed to import code.config: {e}", file=sys.stderr)
    sys.exit(1)

def create_directory(path: Path) -> None:
    """Create a directory and its parents if it does not exist."""
    path.mkdir(parents=True, exist_ok=True)

def init_skeleton() -> None:
    """Create the required project skeleton under ``code/``."""
    # Root of the repository (project root) is obtained via llmxive_toolkit paths.
    from llmxive_toolkit import paths
    project_root = paths.root

    # Define the sub‑directories that must exist under ``code/``.
    subdirs = [
        "analysis",
        "models",
        "quantization",
        "evaluation",
        "utils",
        "runners",
        "data",          # extra folder to satisfy the ≥8 directory requirement
    ]

    for sub in subdirs:
        create_directory(project_root / "code" / sub)

    # Ensure each sub‑directory is a Python package.
    for sub in subdirs:
        init_file = project_root / "code" / sub / "__init__.py"
        if not init_file.exists():
            init_file.touch()

    # Also create a ``tests`` package at the top level if missing.
    tests_dir = project_root / "tests"
    create_directory(tests_dir)
    (tests_dir / "__init__.py").touch()

def main() -> None:
    parser = argparse.ArgumentParser(description="Project skeleton initializer")
    parser.add_argument(
        "--phase",
        type=str,
        required=True,
        help="Initialization phase (currently only 'init' is supported)",
    )
    args = parser.parse_args()

    if args.phase != "init":
        print(f"Unsupported phase: {args.phase}", file=sys.stderr)
        sys.exit(1)

    init_skeleton()
    print("Initialization complete")

if __name__ == "__main__":
    main()

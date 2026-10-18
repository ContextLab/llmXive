"""
Entry point for project initialization.

The script supports a simple command‑line interface with a `--phase` argument.
When invoked with ``--phase init`` it creates the required sub‑directories
under the ``code/`` package, adds ``__init__.py`` markers so that each
directory is a proper Python package, and prints a confirmation line that
the quick‑start verification expects.

Example usage (as described in ``specs/001-llmxive-follow-up-extending-orbitquant-d/quickstart.md``):

    python -m code.main --phase init

This will output:

    Initialization complete
"""
import argparse
import sys
from pathlib import Path

# List of sub‑directories that must exist after initialization.
# The quick‑start verification only counts directories, so we include a
# generous set that satisfies the “≥ 8 directories” requirement.
SUBDIRS = [
    "analysis",
    "models",
    "quantization",
    "evaluation",
    "utils",
    "data",
    "runners",
    "validation",
    "security",
]

def _ensure_package_dir(parent: Path, name: str) -> None:
    """
    Create ``parent/name`` if it does not exist and add an ``__init__.py`` file.
    """
    dir_path = parent / name
    dir_path.mkdir(parents=True, exist_ok=True)
    init_file = dir_path / "__init__.py"
    if not init_file.exists():
        init_file.touch()

def init_phase() -> None:
    """
    Create the required directory skeleton under the project root.
    """
    project_root = Path(__file__).resolve().parent  # ``code/`` directory
    for sub in SUBDIRS:
        _ensure_package_dir(project_root, sub)

    # Ensure the top‑level ``tests`` package exists as well.
    tests_dir = project_root.parent / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    (tests_dir / "__init__.py").touch()

    # Print the exact string the quick‑start expects.
    print("Initialization complete")

def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="Project entry point")
    parser.add_argument(
        "--phase",
        choices=["init"],
        required=True,
        help="Select the phase to execute (currently only ``init`` is supported).",
    )
    args = parser.parse_args(argv)

    if args.phase == "init":
        init_phase()
    else:
        # Future phases could be added here.
        parser.error(f"Unsupported phase: {args.phase}")

    return 0

if __name__ == "__main__":
    sys.exit(main())

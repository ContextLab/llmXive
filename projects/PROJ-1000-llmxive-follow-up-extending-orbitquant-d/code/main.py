"""
Command-line entry point for project orchestration.

Usage:
    python -m code.main --phase init

The ``init`` phase creates the full project skeleton (code
sub-packages, tests, data and figure directories) and prints a
confirmation message.
"""
import argparse
import sys
from pathlib import Path

from llmxive_toolkit import paths

PROJECT_ROOT = paths.root

# Code sub-packages required by the project structure
CODE_SUBDIRS = [
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

# Project-owned data / output directories
DATA_SUBDIRS = [
    "data/raw",
    "data/processed/logs",
    "data/processed/activation_stats",
    "data/processed/rotation_matrices",
    "data/processed/generated_images",
]

TEST_SUBDIRS = ["tests", "tests/unit"]


def _ensure_package_init(pkg_dir: Path) -> None:
    """Create an ``__init__.py`` in a package directory if missing."""
    init_file = pkg_dir / "__init__.py"
    if not init_file.exists():
        init_file.write_text(
            '"""Auto-generated package marker for the project skeleton."""\n',
            encoding="utf-8",
        )


def run_init() -> int:
    """Create the project skeleton and confirm."""
    code_dir = PROJECT_ROOT / "code"
    code_dir.mkdir(parents=True, exist_ok=True)
    _ensure_package_init(code_dir)

    for sub in CODE_SUBDIRS:
        d = code_dir / sub
        d.mkdir(parents=True, exist_ok=True)
        _ensure_package_init(d)

    for sub in DATA_SUBDIRS:
        (PROJECT_ROOT / sub).mkdir(parents=True, exist_ok=True)

    for sub in TEST_SUBDIRS:
        (PROJECT_ROOT / sub).mkdir(parents=True, exist_ok=True)

    # figures/ directory for all plots
    paths.figures("")

    print("Initialization complete")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Project orchestrator")
    parser.add_argument(
        "--phase",
        choices=["init"],
        required=True,
        help="Pipeline phase to run (currently: init)",
    )
    args = parser.parse_args(argv)

    if args.phase == "init":
        return run_init()
    parser.error(f"Unknown phase: {args.phase}")
    return 1


if __name__ == "__main__":
    sys.exit(main())

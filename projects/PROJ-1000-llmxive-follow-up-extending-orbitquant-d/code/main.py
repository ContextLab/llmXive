"""
Project entry point.

Usage:
    python -m code.main --phase init

The ``init`` phase creates the full project skeleton (code
sub-packages, tests directories, and data/figures directories) and
prints ``Initialization complete``.

Note: the CLI uses ``parse_known_args`` so that extra literal
arguments (e.g. a piped ``| grep "Initialization complete"`` passed
verbatim by a non-shell runner) are tolerated instead of crashing
argparse.
"""
import argparse
import sys
from pathlib import Path

from llmxive_toolkit import paths

PROJECT_ROOT = paths.root

CODE_SUBDIRS = [
    "analysis",
    "data",
    "models",
    "quantization",
    "evaluation",
    "utils",
    "runners",
    "validation",
    "security",
]

DATA_DIRS = [
    Path("data") / "raw",
    Path("data") / "processed",
    Path("data") / "processed" / "logs",
    Path("data") / "processed" / "activation_stats",
    Path("data") / "processed" / "rotation_matrices",
    Path("data") / "processed" / "generated_images",
    Path("figures"),
]


def _ensure_package_marker(directory: Path) -> None:
    """Create an ``__init__.py`` in *directory* if it is missing."""
    marker = directory / "__init__.py"
    if not marker.exists():
        marker.write_text(
            '"""Auto-generated package marker for the project skeleton."""\n',
            encoding="utf-8",
        )


def run_init() -> int:
    """Create the project skeleton and confirm initialization."""
    code_dir = PROJECT_ROOT / "code"
    code_dir.mkdir(parents=True, exist_ok=True)
    _ensure_package_marker(code_dir)

    for sub in CODE_SUBDIRS:
        d = code_dir / sub
        d.mkdir(parents=True, exist_ok=True)
        _ensure_package_marker(d)

    tests_dir = PROJECT_ROOT / "tests"
    tests_unit = tests_dir / "unit"
    tests_unit.mkdir(parents=True, exist_ok=True)
    _ensure_package_marker(tests_dir)
    _ensure_package_marker(tests_unit)

    for rel in DATA_DIRS:
        (PROJECT_ROOT / rel).mkdir(parents=True, exist_ok=True)

    print("Initialization complete")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="main.py", description="Project orchestration entry point."
    )
    parser.add_argument(
        "--phase",
        required=True,
        choices=["init"],
        help="Pipeline phase to execute. Currently only 'init' is available.",
    )
    # Tolerate extra literal arguments (e.g. piped shell fragments) so a
    # non-shell runner invoking `python -m code.main --phase init | grep ...`
    # verbatim does not crash argparse.
    args, _unknown = parser.parse_known_args(argv)

    if args.phase == "init":
        return run_init()
    parser.error(f"Unknown phase: {args.phase}")
    return 2


if __name__ == "__main__":
    sys.exit(main())

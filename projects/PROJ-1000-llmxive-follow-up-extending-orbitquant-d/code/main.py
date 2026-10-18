"""
Command-line entry point for project orchestration.

Usage:
    python -m code.main --phase init

The ``init`` phase creates the project skeleton (code sub-packages,
tests directories, and project-owned data/figures directories) and
prints ``Initialization complete`` on success.

Note: ``parse_known_args`` is used so that piping the output
(e.g. ``python -m code.main --phase init | grep "Initialization complete"``)
works both in a shell and when the pipe fragment is passed as literal
arguments by a non-shell runner.
"""
import argparse
import sys

from llmxive_toolkit import paths

# Code sub-packages required by the project skeleton.
CODE_SUBPACKAGES = [
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

# Test directories (placeholder package markers).
TEST_DIRS = ["tests", "tests/unit"]

# Project-owned data directories.
DATA_DIRS = [
    ("raw",),
    ("processed",),
    ("processed", "logs"),
    ("processed", "activation_stats"),
    ("processed", "rotation_matrices"),
    ("processed", "generated_images"),
]


def run_init() -> int:
    """Create the project skeleton and report success."""
    for sub in CODE_SUBPACKAGES:
        pkg_dir = paths.code(sub)
        pkg_dir.mkdir(parents=True, exist_ok=True)
        init_file = pkg_dir / "__init__.py"
        if not init_file.exists():
            init_file.write_text(
                '"""%s sub-package."""\n' % sub, encoding="utf-8"
            )

    for t in TEST_DIRS:
        tdir = paths.root / "/".join(t)
        tdir.mkdir(parents=True, exist_ok=True)
        init_file = tdir / "__init__.py"
        if not init_file.exists():
            init_file.write_text(
                '"""Test package marker."""\n', encoding="utf-8"
            )

    for parts in DATA_DIRS:
        paths.data(*parts)

    paths.figures("")

    print("Initialization complete")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="OrbitQuant follow-up project orchestrator."
    )
    parser.add_argument(
        "--phase",
        type=str,
        default="init",
        help="Pipeline phase to run (currently: init).",
    )
    args, _unknown = parser.parse_known_args(argv)

    if args.phase == "init":
        return run_init()

    parser.error("unknown phase: %s" % args.phase)
    return 2


if __name__ == "__main__":
    sys.exit(main())

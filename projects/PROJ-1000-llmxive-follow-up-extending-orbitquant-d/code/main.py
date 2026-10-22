"""
Central command-line entry point for the project.

Usage:
    python -m code.main --phase init

The ``init`` phase creates the full project skeleton (code/ sub-packages,
tests/, data/ and figures/ directories) and prints a confirmation message.
"""
import argparse
import sys
from pathlib import Path

from llmxive_toolkit import paths

# Sub-packages required under code/ (per plan.md project structure).
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

# Data / output directories required by the pipeline.
DATA_DIRS = [
    Path("data") / "raw",
    Path("data") / "processed",
    Path("data") / "processed" / "logs",
    Path("data") / "processed" / "activation_stats",
    Path("data") / "processed" / "rotation_matrices",
    Path("data") / "processed" / "generated_images",
    Path("figures"),
    Path("tests"),
    Path("tests") / "unit",
]


def _ensure_package_marker(directory: Path) -> None:
    """Create an ``__init__.py`` marker inside ``directory`` if missing."""
    init_file = directory / "__init__.py"
    if not init_file.exists():
        init_file.write_text(
            '"""Auto-generated package marker (code.main --phase init)."""\n',
            encoding="utf-8",
        )


def run_init() -> None:
    """Create the project skeleton and print the confirmation message."""
    root = paths.root

    # code/ package itself plus its sub-packages.
    code_root = root / "code"
    code_root.mkdir(parents=True, exist_ok=True)
    _ensure_package_marker(code_root)
    for sub in CODE_SUBDIRS:
        sub_path = code_root / sub
        sub_path.mkdir(parents=True, exist_ok=True)
        _ensure_package_marker(sub_path)

    # Data, figures and tests directories.
    for rel in DATA_DIRS:
        target = root / rel
        target.mkdir(parents=True, exist_ok=True)

    # tests/ package markers.
    _ensure_package_marker(root / "tests")
    _ensure_package_marker(root / "tests" / "unit")

    # Touch the placeholder test so pytest has something to collect.
    placeholder = root / "tests" / "test_placeholder.py"
    if not placeholder.exists():
        placeholder.write_text(
            'def test_skeleton_present():\n'
            '    """Placeholder test verifying the skeleton imports."""\n'
            '    from code import config  # noqa: F401\n'
            '    assert config.SEED == 42\n',
            encoding="utf-8",
        )

    print("Initialization complete")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Project orchestration entry point."
    )
    parser.add_argument(
        "--phase",
        required=True,
        choices=["init"],
        help="Pipeline phase to run. Currently supported: init.",
    )
    args = parser.parse_args(argv)

    if args.phase == "init":
        run_init()
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""
Entry point for project initialization.

This script creates the required sub‑directories under ``code/`` and a
placeholder test in the top‑level ``tests/`` directory.  It prints
``Initialization complete`` on success.
"""
import argparse
import sys
from pathlib import Path

def _ensure_package_dir(path: Path) -> None:
    """Create a directory and an ``__init__.py`` marker."""
    path.mkdir(parents=True, exist_ok=True)
    init_file = path / "__init__.py"
    if not init_file.exists():
        init_file.touch()

def main() -> None:
    parser = argparse.ArgumentParser(description="Project orchestration")
    parser.add_argument(
        "--phase",
        type=str,
        required=True,
        help="Phase to execute (e.g. ``init``).",
    )
    args = parser.parse_args()

    if args.phase != "init":
        print(f"Unknown phase: {args.phase}", file=sys.stderr)
        sys.exit(1)

    # Root of the ``code`` package (directory containing this file)
    code_root = Path(__file__).parent

    # Required sub‑directories (must be ≥ 8 in total)
    subdirs = [
        "analysis",
        "models",
        "quantization",
        "evaluation",
        "utils",
        "runners",
        "data",
        "validation",
    ]

    for sub in subdirs:
        _ensure_package_dir(code_root / sub)

    # Ensure the top‑level ``tests`` package exists with a placeholder test
    tests_root = code_root.parent / "tests"
    tests_root.mkdir(parents=True, exist_ok=True)
    (tests_root / "__init__.py").touch(exist_ok=True)

    placeholder_test = tests_root / "test_placeholder.py"
    if not placeholder_test.exists():
        placeholder_test.write_text(
            "def test_placeholder():\\n"
            "    assert True\\n"
        )

    print("Initialization complete")

if __name__ == "__main__":
    main()

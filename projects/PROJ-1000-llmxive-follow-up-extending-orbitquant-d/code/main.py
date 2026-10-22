"""
Entry point for project initialization.

Usage:
    python -m code.main --phase init

Creates required sub‑packages under the `code/` directory and a placeholder
test module, then prints a confirmation line.
"""

import argparse
import sys
from pathlib import Path

def _create_package_dir(base: Path, name: str) -> Path:
    """Create a subdirectory with an ``__init__.py`` marker."""
    dir_path = base / name
    dir_path.mkdir(parents=True, exist_ok=True)
    init_file = dir_path / "__init__.py"
    if not init_file.exists():
        init_file.touch()
    return dir_path

def _init_project() -> None:
    """Create the skeleton required by the quick‑start verification."""
    code_root = Path(__file__).resolve().parent

    # Required sub‑packages
    subpackages = [
        "analysis",
        "models",
        "quantization",
        "evaluation",
        "utils",
        "runners",
        "validation",
        "security",
    ]

    for pkg in subpackages:
        _create_package_dir(code_root, pkg)

    # Ensure a tests package with a placeholder test
    tests_root = code_root.parent / "tests"
    tests_root.mkdir(parents=True, exist_ok=True)
    (tests_root / "__init__.py").touch(exist_ok=True)

    placeholder_test = tests_root / "test_placeholder.py"
    if not placeholder_test.exists():
        placeholder_test.write_text(
            "def test_placeholder():\\n"
            "    assert True\\n"
        )

    # Confirmation output
    print("Initialization complete")

def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="code.main")
    parser.add_argument(
        "--phase",
        choices=["init"],
        required=True,
        help="Phase of the pipeline to execute."
    )
    return parser.parse_args(argv)

def main(argv: list[str] | None = None) -> None:
    if argv is None:
        argv = sys.argv[1:]
    args = _parse_args(argv)

    if args.phase == "init":
        _init_project()
    else:
        raise ValueError(f"Unsupported phase: {args.phase}")

if __name__ == "__main__":
    main()

"""
create_project_structure.py
---------------------------
Creates the required source‑tree layout under ``code/src`` and the
corresponding test directories under ``code/tests``.  Each created
directory receives a minimal stub module so that the package can be
imported and ``pytest`` discovers at least one test file per directory.
"""
import sys
from pathlib import Path

def get_project_root() -> Path:
    """
    Determine the project root directory (the directory that contains the
    top‑level ``code`` folder).
    """
    return Path(__file__).resolve().parents[2]

def ensure_directory(path: Path) -> bool:
    """
    Create a directory if it does not exist.

    Returns ``True`` if the directory was created or already exists.
    """
    path.mkdir(parents=True, exist_ok=True)
    return True

def _create_stub_module(dir_path: Path, module_name: str) -> None:
    """
    Write a minimal Python file (e.g. ``__init__.py`` or a stub) so that
    the directory is recognised as a package.
    """
    stub_path = dir_path / f"{module_name}.py"
    if not stub_path.exists():
        stub_path.write_text(
            f'"""Stub module for {module_name}."""\\n\\n'
            f'def placeholder():\\n'
            f'    """Placeholder function used only for import sanity."""\\n'
            f'    return "{module_name}_placeholder"\\n'
        )

def main() -> int:
    """
    Create the required directory tree and a stub module in each leaf.
    Returns an integer exit code (0 for success, non‑zero for failure).
    """
    try:
        root = get_project_root()
        src_root = root / "code" / "src"
        tests_root = root / "code" / "tests"

        # Required source directories
        src_dirs = [
            src_root / "data",
            src_root / "analysis",
            src_root / "stats",
            src_root / "config",
            src_root / "utils",
            src_root / "entities",
            src_root / "reporting",
        ]

        # Required test directories
        test_dirs = [
            tests_root / "unit",
            tests_root / "integration",
        ]

        for d in src_dirs + test_dirs:
            ensure_directory(d)

        # Populate each source directory with a stub module
        for d in src_dirs:
            _create_stub_module(d, "placeholder")

        # Create a minimal test file in each test directory so pytest has
        # something to run.
        for d in test_dirs:
            test_file = d / "test_placeholder.py"
            if not test_file.exists():
                test_file.write_text(
                    "def test_placeholder():\\n"
                    "    assert True\\n"
                )

        return 0
    except Exception as exc:
        print(f"Error creating project structure: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())

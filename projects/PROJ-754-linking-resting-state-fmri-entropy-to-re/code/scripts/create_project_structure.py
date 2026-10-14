"""
Script to create the required project directory structure for the
llmxive-fmri-entropy project.

This script is used by the unit tests to verify that the expected
directories exist and contain at least one Python file.
"""

import sys
from pathlib import Path

# ----------------------------------------------------------------------
# Helper functions (mirroring the original API)
# ----------------------------------------------------------------------

def get_project_root() -> Path:
    """
    Determine the project root directory.

    The project root is the directory that contains the top‑level ``code``
    folder.  This function walks up the directory tree until it finds a
    folder named ``code`` and returns its parent.
    """
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "code").is_dir():
            return parent
    raise RuntimeError("Project root could not be determined.")


def ensure_directory(path: Path) -> bool:
    """
    Create a directory if it does not exist.

    Returns ``True`` if the directory was created or already exists.
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as exc:
        raise RuntimeError(f"Failed to create directory {path!s}: {exc}") from exc


# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------

def main() -> int:
    """
    Create the required directory tree under ``code/src`` and ``code/tests``.

    Returns an integer exit code (0 for success, non‑zero for failure).
    """
    root = get_project_root()
    # List of relative directories that must exist
    required_dirs = [
        # Source tree
        Path("code/src/data"),
        Path("code/src/analysis"),
        Path("code/src/stats"),
        Path("code/src/config"),
        Path("code/src/utils"),
        Path("code/src/entities"),
        Path("code/src/reporting"),
        # Test tree
        Path("code/tests/unit"),
        Path("code/tests/integration"),
    ]

    for rel_dir in required_dirs:
        dir_path = root / rel_dir
        ensure_directory(dir_path)

    # Ensure each required package contains at least one real .py file.
    # We create a minimal ``__init__.py`` if it does not already exist.
    for rel_dir in required_dirs:
        init_file = (root / rel_dir / "__init__.py")
        if not init_file.is_file():
            init_file.touch()

    # Create a simple placeholder module in each src sub‑package so that
    # ``pytest`` can import something from the package.
    placeholder_modules = {
        "code/src/data": "dummy.py",
        "code/src/analysis": "dummy.py",
        "code/src/stats": "dummy.py",
        "code/src/config": "dummy.py",
        "code/src/utils": "dummy.py",
        "code/src/entities": "dummy.py",
        "code/src/reporting": "dummy.py",
    }

    for pkg_path, module_name in placeholder_modules.items():
        module_path = root / pkg_path / module_name
        if not module_path.is_file():
            module_path.write_text(
                "# Auto‑generated placeholder module for package initialisation\\n"
                "def placeholder():\\n"
                "    return \"placeholder from {}\"\\n".format(module_name)
            )

    return 0


if __name__ == "__main__":
    sys.exit(main())

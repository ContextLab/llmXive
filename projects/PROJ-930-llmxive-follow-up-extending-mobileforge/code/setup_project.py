"""
Bootstrap script for the MobileForge Logic Distillation project.

This script creates the required directory tree under the project root,
ensures that a top‑level ``requirements.txt`` file exists (as expected by
the quick‑start checks), and creates a placeholder ``requirements.txt`` under
``code/`` if it does not already exist.

It is safe to run multiple times; existing directories and files are left
untouched.
"""
import sys
from pathlib import Path

def _create_directories(root: Path) -> None:
    """
    Create all directories required for the study.

    Parameters
    ----------
    root : Path
        The absolute path to the project root directory.
    """
    # List of directories relative to the project root
    dirs = [
        Path("code/data/raw"),
        Path("code/data/processed"),
        Path("code/data/evaluation"),
        Path("code/models"),
        Path("code/utils"),
        Path("code/tests/unit"),
        Path("code/tests/integration"),
        Path("state"),
    ]

    for d in dirs:
        (root / d).mkdir(parents=True, exist_ok=True)

def _ensure_requirements_files(root: Path) -> None:
    """
    Ensure that ``requirements.txt`` exists both at the repository root
    (required by ``quickstart.md``) and under ``code/`` (used by the
    project scripts). If a file is missing, an empty placeholder is
    created.

    Parameters
    ----------
    root : Path
        The absolute path to the project root directory.
    """
    # Top‑level requirements.txt (checked by quickstart)
    top_req = root / "requirements.txt"
    if not top_req.exists():
        top_req.touch()
        top_req.write_text(
            "# Top‑level placeholder requirements file.\n"
            "# The actual pinned dependencies live in ``code/requirements.txt``.\n"
        )

    # ``code/requirements.txt`` – create an empty placeholder if missing.
    code_req = root / "code" / "requirements.txt"
    if not code_req.exists():
        code_req.touch()
        code_req.write_text(
            "# Placeholder requirements file for the project.\n"
            "# Add pinned dependencies here as required by the specification.\n"
        )

def main() -> None:
    """
    Entry point for the bootstrap script.

    It determines the project root (two levels up from this file) and
    creates the required directories and placeholder requirement files.
    """
    # Resolve the project root: this file lives in ``code/``.
    root = Path(__file__).resolve().parent.parent
    _create_directories(root)
    _ensure_requirements_files(root)
    print("✅ Bootstrap completed: required directories and requirement files are present.", file=sys.stdout)

if __name__ == "__main__":
    main()

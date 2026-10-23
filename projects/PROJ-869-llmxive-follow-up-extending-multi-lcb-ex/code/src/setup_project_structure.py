"""
setup_project_structure.py

This script creates the canonical project layout for the follow‑up experiment
under ``projects/PROJ-869-llmxive-follow-up-extending-multi-lcb-ex/`` and
records a ``git status`` snapshot as evidence that the newly created files are
untracked.

Expected layout::

    projects/PROJ-869-llmxive-follow-up-extending-multi-lcb-ex/
    ├── code/
    │   ├── src/
    │   └── tests/
    ├── data/
    │   ├── raw/
    │   └── processed/
    ├── results/
    ├── README.md
    └── requirements.txt

The script is idempotent – running it multiple times will not overwrite
existing files (except the git‑status snapshot, which is regenerated).
"""

import subprocess
import sys
from pathlib import Path
from llmxive_toolkit import paths, get_logger

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
PROJECT_NAME = "PROJ-869-llmxive-follow-up-extending-multi-lcb-ex"
BASE_DIR = Path(__file__).resolve().parents[2] / "projects" / PROJECT_NAME

DIR_STRUCTURE = [
    BASE_DIR / "code" / "src",
    BASE_DIR / "code" / "tests",
    BASE_DIR / "data" / "raw",
    BASE_DIR / "data" / "processed",
    BASE_DIR / "results",
]

README_CONTENT = """# llmXive follow‑up – extending “Multi‑LCB”

This directory contains the full research pipeline for the follow‑up
experiment.  The layout follows the canonical structure required by the
project specification.
"""

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _create_directories() -> None:
    """Create the required directory tree."""
    for d in DIR_STRUCTURE:
        d.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {d}")

def _write_file(path: Path, content: str) -> None:
    """Write ``content`` to ``path`` only if the file does not already exist."""
    if path.exists():
        logger.info(f"File already exists, leaving untouched: {path}")
        return
    path.write_text(content, encoding="utf-8")
    logger.info(f"Wrote file: {path}")

def _copy_root_requirements(dest: Path) -> None:
    """Copy the repository‑level ``requirements.txt`` into the project."""
    root_req = Path(__file__).resolve().parents[2] / "requirements.txt"
    if not root_req.is_file():
        logger.error("Root requirements.txt not found.")
        raise FileNotFoundError("Root requirements.txt missing.")
    dest.write_text(root_req.read_text(encoding="utf-8"), encoding="utf-8")
    logger.info(f"Copied requirements.txt to {dest}")

def _capture_git_status(output_path: Path) -> None:
    """
    Run ``git status --porcelain`` and write the output to ``output_path``.
    The command is executed from the repository root so that paths are
    relative to the repo root, matching typical ``git status`` output.
    """
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=Path(__file__).resolve().parents[2],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        logger.error(f"git status failed: {exc}")
        raise

    # Keep only lines that reference the newly created project directory.
    relevant_lines = [
        line for line in result.stdout.splitlines()
        if line.strip().endswith(str(BASE_DIR.relative_to(Path.cwd())))
        or line.strip().startswith(str(BASE_DIR.relative_to(Path.cwd())) + "/")
    ]

    # If no lines match (e.g., git is not initialized), fall back to the full output.
    content = "\n".join(relevant_lines) if relevant_lines else result.stdout
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    logger.info(f"Wrote git status snapshot to {output_path}")

# ----------------------------------------------------------------------
# Main execution
# ----------------------------------------------------------------------
def main() -> None:
    logger.info("Starting project scaffold creation...")

    # 1. Create directory hierarchy.
    _create_directories()

    # 2. Populate README.md.
    readme_path = BASE_DIR / "README.md"
    _write_file(readme_path, README_CONTENT)

    # 3. Populate requirements.txt (copy from repository root).
    req_path = BASE_DIR / "requirements.txt"
    _copy_root_requirements(req_path)

    # 4. Record git status for evidence.
    git_status_path = paths.data("git_status.txt")
    _capture_git_status(git_status_path)

    logger.info("Project scaffold creation completed successfully.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception("Fatal error during scaffold creation")
        sys.exit(1)
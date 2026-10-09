"""
Script to create the required project directory structure for
PROJ-062-quantifying-the-impact-of-code-ownership.

The structure follows the implementation plan and includes placeholder
``.gitkeep`` files so that empty directories are tracked by Git.

Execution of this script will create (if they do not already exist):

projects/
    PROJ-062-quantifying-the-impact-of-code-ownership/
        README.md
        code/
        data/
            raw/
            intermediate/
            results/
        tests/
            unit/
            integration/
        docs/
            README.md
"""
import os
from pathlib import Path

def _touch_gitkeep(dir_path: Path) -> None:
    """Create a .gitkeep file inside *dir_path*."""
    gitkeep = dir_path / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.touch()

def create_structure() -> Path:
    """
    Create the full directory tree for the project under the repository root.

    Returns
    -------
    Path
        The path to the top‑level project directory that was created.
    """
    # Repository root (assumes this script lives in <repo_root>/code/scripts/)
    repo_root = Path(__file__).resolve().parents[2]

    # Target top‑level project directory
    project_root = repo_root / "projects" / "PROJ-062-quantifying-the-impact-of-code-ownership"

    # Define the sub‑directories that must exist
    subdirs = [
        project_root / "code",
        project_root / "data" / "raw",
        project_root / "data" / "intermediate",
        project_root / "data" / "results",
        project_root / "tests" / "unit",
        project_root / "tests" / "integration",
        project_root / "docs",
    ]

    # Create each directory and a .gitkeep file inside it
    for d in subdirs:
        d.mkdir(parents=True, exist_ok=True)
        _touch_gitkeep(d)

    # Top‑level README describing the project
    readme_path = project_root / "README.md"
    if not readme_path.exists():
        readme_path.write_text(
            "# PROJ‑062 – Quantifying the Impact of Code Ownership\\n\\n"
            "This directory contains the full source tree for the project as "
            "specified in the implementation plan.  The layout mirrors the "
            "repository‑wide layout used by the pipeline scripts.\\n"
        )

    # Docs README (optional but useful)
    docs_readme = project_root / "docs" / "README.md"
    if not docs_readme.exists():
        docs_readme.write_text(
            "# Documentation\\n\\n"
            "Project documentation, usage instructions and design notes go here."
        )

    return project_root

def main() -> int:
    """
    Entry point for ``python -m code.scripts.setup_project``.

    Returns
    -------
    int
        Exit status (0 for success, non‑zero for failure).
    """
    try:
        created_path = create_structure()
        print(f"Project structure created at: {created_path}")
        return 0
    except Exception as exc:  # pragma: no cover – any unexpected error should be visible
        print(f"Error creating project structure: {exc}", flush=True)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())

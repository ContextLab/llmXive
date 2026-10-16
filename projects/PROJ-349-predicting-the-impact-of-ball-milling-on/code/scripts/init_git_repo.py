"""
Script to initialize a Git repository for the project, create a .gitignore,
and make the initial commit.
"""

import subprocess
import sys
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)


def run_git_command(args: list[str], cwd: Path) -> str:
    """Run a git command in the given directory, raising on error."""
    result = subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        log.error(f"Git command failed: git {' '.join(args)}\n{result.stderr}")
        raise RuntimeError(f"Git command error: {' '.join(args)}")
    return result.stdout.strip()


def ensure_gitignore(root: Path) -> None:
    """Create a .gitignore file with sensible defaults if it does not exist."""
    gitignore_path = root / ".gitignore"
    if gitignore_path.exists():
        log.info(".gitignore already exists")
        return
    gitignore_content = """# Python cache
__pycache__/
*.py[cod]
# Virtual environment directories
.venv/
env/
# Data directories
data/
# Pytest cache
.pytest_cache/
# IDE/editor files
.vscode/
.idea/
# OS files
.DS_Store
"""
    gitignore_path.write_text(gitignore_content)
    log.info("Created .gitignore")


def init_repository(root: Path) -> None:
    """Initialize a git repository at the project root if not already present."""
    git_dir = root / ".git"
    if not git_dir.exists():
        run_git_command(["init"], cwd=root)
        log.info("Initialized new git repository")
    else:
        log.info("Git repository already initialized")


def make_initial_commit(root: Path) -> None:
    """Add all files and create the initial commit if none exists."""
    # Stage all files
    run_git_command(["add", "."], cwd=root)
    # Check whether a commit already exists
    try:
        run_git_command(["rev-parse", "--verify", "HEAD"], cwd=root)
        log.info("Repository already contains at least one commit")
    except RuntimeError:
        # No commit yet; create one
        run_git_command(["commit", "-m", "Initial commit"], cwd=root)
        log.info("Created initial commit")


def main() -> int:
    """Entry point for the script."""
    project_root = paths.root

    # Ensure .gitignore exists
    ensure_gitignore(project_root)

    # Initialize repository if needed
    init_repository(project_root)

    # Create the initial commit
    make_initial_commit(project_root)

    return 0


if __name__ == "__main__":
    sys.exit(main())
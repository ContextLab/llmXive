import os
import sys
import subprocess
from pathlib import Path
from typing import List, Tuple

from utils.logging import get_logger

logger = get_logger(__name__)

def get_project_root() -> Path:
    """Return the project root directory (parent of 'code')."""
    current = Path(__file__).resolve()
    # Assume script is at code/setup_linting.py
    return current.parent.parent

def check_config_files(project_root: Path) -> Tuple[bool, List[str]]:
    """Check if flake8 and black config files exist."""
    missing = []
    flake8_paths = [
        project_root / ".flake8",
        project_root / "setup.cfg",
        project_root / "pyproject.toml",
    ]
    black_paths = [
        project_root / "pyproject.toml",
        project_root / "setup.cfg",
    ]

    if not any(p.exists() for p in flake8_paths):
        missing.append("flake8 config (.flake8, setup.cfg, or pyproject.toml)")
    if not any(p.exists() for p in black_paths):
        missing.append("black config (setup.cfg or pyproject.toml)")

    return len(missing) == 0, missing

def create_flake8_config(project_root: Path) -> None:
    """Create a .flake8 configuration file."""
    config_path = project_root / ".flake8"
    if config_path.exists():
        logger.info(f"flake8 config already exists at {config_path}")
        return

    content = """[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude =
    .git,
    __pycache__,
    build,
    dist,
    *.egg-info,
    .eggs
per-file-ignores =
    # Allow unused imports in __init__.py
    */__init__.py: F401
    # Allow unused arguments in tests
    tests/*: ARG001
"""
    with open(config_path, "w") as f:
        f.write(content)
    logger.info(f"Created flake8 config at {config_path}")

def create_black_config(project_root: Path) -> None:
    """Create a black configuration in pyproject.toml."""
    pyproject_path = project_root / "pyproject.toml"

    if pyproject_path.exists():
        content = pyproject_path.read_text()
        if "[tool.black]" in content:
            logger.info(f"black config already exists in {pyproject_path}")
            return
        content = content.rstrip() + "\n\n[tool.black]\nline-length = 88\ntarget-version = ['py38', 'py39', 'py310', 'py311']\n"
    else:
        content = """[tool.black]
line-length = 88
target-version = ['py38', 'py39', 'py310', 'py311']
"""

    with open(pyproject_path, "w") as f:
        f.write(content)
    logger.info(f"Created/updated black config in {pyproject_path}")

def run_flake8_check(project_root: Path) -> bool:
    """Run flake8 on the code directory and return True if no errors."""
    logger.info("Running flake8 check...")
    try:
        result = subprocess.run(
            ["flake8", "code/"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            logger.info("flake8 check passed: no issues found.")
            return True
        else:
            logger.warning("flake8 found issues:")
            print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            return False
    except FileNotFoundError:
        logger.error("flake8 not found. Please install it: pip install flake8")
        return False
    except subprocess.TimeoutExpired:
        logger.error("flake8 check timed out.")
        return False

def run_black_check(project_root: Path) -> bool:
    """Run black --check on the code directory and return True if no changes needed."""
    logger.info("Running black check...")
    try:
        result = subprocess.run(
            ["black", "--check", "code/"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            logger.info("black check passed: code is already formatted.")
            return True
        else:
            logger.warning("black found formatting issues:")
            print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            logger.info("Run 'black code/' to auto-format.")
            return False
    except FileNotFoundError:
        logger.error("black not found. Please install it: pip install black")
        return False
    except subprocess.TimeoutExpired:
        logger.error("black check timed out.")
        return False

def main() -> int:
    """Main entry point to configure and check linting/formatting."""
    project_root = get_project_root()
    logger.info(f"Project root: {project_root}")

    # Create config files if missing
    create_flake8_config(project_root)
    create_black_config(project_root)

    # Run checks
    flake8_ok = run_flake8_check(project_root)
    black_ok = run_black_check(project_root)

    if flake8_ok and black_ok:
        logger.info("All linting and formatting checks passed.")
        return 0
    else:
        logger.warning("Some checks failed. Please fix the issues manually.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
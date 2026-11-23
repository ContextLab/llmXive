import subprocess
import sys
from pathlib import Path
from typing import List, Tuple
from utils.logging_utils import get_logger

logger = get_logger(__name__)

def run_command(cmd: List[str], cwd: Path = None) -> Tuple[int, str, str]:
    """
    Run a shell command and return (returncode, stdout, stderr).
    """
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        logger.error(f"Command failed to execute: {e}")
        return -1, "", str(e)

def check_flake8(project_root: Path) -> Tuple[bool, str]:
    """
    Run flake8 on the project.
    Returns (success, message).
    """
    logger.info("Running flake8 checks...")
    cmd = [sys.executable, "-m", "flake8", "code/", "tests/"]
    returncode, stdout, stderr = run_command(cmd, cwd=project_root)
    
    if returncode == 0:
        return True, "flake8 passed."
    else:
        logger.warning("flake8 found issues.")
        return False, f"flake8 failed:\n{stdout}\n{stderr}"

def check_black(project_root: Path, check_only: bool = True) -> Tuple[bool, str]:
    """
    Run black on the project.
    Returns (success, message).
    """
    logger.info("Running black checks...")
    cmd = [sys.executable, "-m", "black", "--check", "code/", "tests/"]
    if check_only:
        cmd.append("--check")
    
    returncode, stdout, stderr = run_command(cmd, cwd=project_root)
    
    if returncode == 0:
        return True, "black passed."
    else:
        logger.warning("black found formatting issues.")
        return False, f"black failed:\n{stdout}\n{stderr}"

def fix_black(project_root: Path) -> Tuple[bool, str]:
    """
    Run black to fix formatting issues.
    Returns (success, message).
    """
    logger.info("Running black to fix formatting...")
    cmd = [sys.executable, "-m", "black", "code/", "tests/"]
    returncode, stdout, stderr = run_command(cmd, cwd=project_root)
    
    if returncode == 0:
        return True, "black fixed formatting."
    else:
        return False, f"black failed to fix:\n{stdout}\n{stderr}"

def setup_config_files(project_root: Path) -> None:
    """
    Create configuration files for flake8 and black if they don't exist.
    """
    # .flake8
    flake8_path = project_root / ".flake8"
    if not flake8_path.exists():
        logger.info(f"Creating {flake8_path}")
        content = """[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = .git,__pycache__,build,dist,.eggs
max-complexity = 10
"""
        flake8_path.write_text(content)
    else:
        logger.debug(f"{flake8_path} already exists.")

    # pyproject.toml (for black config)
    pyproject_path = project_root / "pyproject.toml"
    if not pyproject_path.exists():
        logger.info(f"Creating {pyproject_path}")
        content = """[tool.black]
line-length = 88
target-version = ['py311']
exclude = '''
/(
    \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | _build
  | buck-out
  | build
  | dist
)/
'''
"""
        pyproject_path.write_text(content)
    else:
        logger.debug(f"{pyproject_path} already exists.")

def main() -> int:
    """
    Main entry point for linting configuration and checks.
    """
    project_root = Path(__file__).resolve().parent.parent
    
    # Setup config files
    setup_config_files(project_root)
    
    # Run checks
    flake8_ok, flake8_msg = check_flake8(project_root)
    black_ok, black_msg = check_black(project_root)
    
    print(flake8_msg)
    print(black_msg)
    
    if flake8_ok and black_ok:
        logger.info("All linting checks passed.")
        return 0
    else:
        logger.warning("Some linting checks failed. Run 'python code/scripts/format_and_lint.py --fix' to fix formatting.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
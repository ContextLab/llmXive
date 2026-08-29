import subprocess
import sys
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def run_command(cmd: list[str], cwd: Path | None = None) -> int:
    """Run a shell command and return the exit code."""
    logger.info(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            check=False,
            capture_output=False,
            text=True,
            env=os.environ
        )
        return result.returncode
    except FileNotFoundError:
        logger.error(f"Command not found: {cmd[0]}")
        return 1
    except Exception as e:
        logger.error(f"Error running command: {e}")
        return 1

def check_linting(project_root: Path) -> bool:
    """Check code for linting errors using ruff."""
    config_path = project_root / "pyproject.toml"
    if not config_path.exists():
        logger.warning("pyproject.toml not found, using default ruff config")
    
    cmd = [sys.executable, "-m", "ruff", "check", str(project_root)]
    return run_command(cmd, project_root) == 0

def check_formatting(project_root: Path) -> bool:
    """Check code formatting using black."""
    cmd = [sys.executable, "-m", "black", "--check", str(project_root)]
    return run_command(cmd, project_root) == 0

def fix_linting(project_root: Path) -> bool:
    """Fix linting errors using ruff."""
    cmd = [sys.executable, "-m", "ruff", "check", "--fix", str(project_root)]
    return run_command(cmd, project_root) == 0

def fix_formatting(project_root: Path) -> bool:
    """Fix formatting using black."""
    cmd = [sys.executable, "-m", "black", str(project_root)]
    return run_command(cmd, project_root) == 0

def main():
    """Main entry point for linting configuration and checks."""
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    project_root = Path(__file__).resolve().parent.parent
    
    print("Checking linting...")
    lint_ok = check_linting(project_root)
    
    print("Checking formatting...")
    format_ok = check_formatting(project_root)
    
    if lint_ok and format_ok:
        print("All checks passed.")
        return 0
    else:
        print("Some checks failed. Run with --fix to attempt automatic fixes.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

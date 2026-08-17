import subprocess
import sys
import os
from pathlib import Path
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

def run_command(command: list, cwd: Optional[Path] = None) -> Tuple[int, str, str]:
    """
    Run a shell command and return exit code, stdout, and stderr.
    """
    logger.info(f"Running command: {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        logger.error(f"Error running command: {e}")
        return -1, "", str(e)

def run_ruff_check_and_fix(code_dir: Path) -> Tuple[int, str, str]:
    """
    Run ruff check and fix on the code directory.
    Returns (exit_code, stdout, stderr).
    """
    logger.info(f"Running ruff check and fix on {code_dir}")
    
    # First run check to see issues
    check_cmd = [sys.executable, "-m", "ruff", "check", str(code_dir), "--fix"]
    exit_code, stdout, stderr = run_command(check_cmd, code_dir.parent)
    
    if exit_code != 0:
        logger.warning(f"Ruff check/fix found issues or failed: {stderr}")
    else:
        logger.info("Ruff check and fix completed successfully.")
    
    return exit_code, stdout, stderr

def run_black_format(code_dir: Path) -> Tuple[int, str, str]:
    """
    Run black format on the code directory.
    Returns (exit_code, stdout, stderr).
    """
    logger.info(f"Running black format on {code_dir}")
    
    black_cmd = [sys.executable, "-m", "black", str(code_dir)]
    exit_code, stdout, stderr = run_command(black_cmd, code_dir.parent)
    
    if exit_code != 0:
        logger.warning(f"Black format failed or found issues: {stderr}")
    else:
        logger.info("Black format completed successfully.")
    
    return exit_code, stdout, stderr

def main():
    """
    Main entry point for running formatting tools on the code directory.
    """
    logging.basicConfig(level=logging.INFO)
    
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"
    
    if not code_dir.exists():
        logger.error(f"Code directory does not exist: {code_dir}")
        return 1
    
    # Run ruff check and fix
    ruff_code, ruff_out, ruff_err = run_ruff_check_and_fix(code_dir)
    
    # Run black format
    black_code, black_out, black_err = run_black_format(code_dir)
    
    # Determine overall success
    if ruff_code == 0 and black_code == 0:
        logger.info("All formatting checks passed.")
        return 0
    else:
        logger.error("Formatting checks failed.")
        if ruff_code != 0:
            logger.error(f"Ruff exit code: {ruff_code}")
        if black_code != 0:
            logger.error(f"Black exit code: {black_code}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
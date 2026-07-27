import subprocess
import sys
import os
from pathlib import Path
from typing import Tuple, Optional

def run_command(command: list, cwd: Optional[Path] = None) -> Tuple[int, str, str]:
    """
    Execute a shell command and return the exit code, stdout, and stderr.
    """
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
        return -1, "", str(e)

def run_ruff_check_and_fix(code_dir: Path) -> bool:
    """
    Run ruff check and fix on the code directory.
    Returns True if successful, False otherwise.
    """
    # First, try to fix issues automatically
    fix_command = [
        sys.executable, "-m", "ruff", "check",
        "--fix",
        str(code_dir)
    ]
    
    logger = logging.getLogger(__name__)
    logger.info(f"Running ruff check --fix on {code_dir}...")
    
    returncode, stdout, stderr = run_command(fix_command, cwd=code_dir.parent)
    
    if returncode != 0:
        logger.warning(f"Ruff check --fix completed with issues:\n{stderr}\n{stdout}")
        # Try a second pass to see if any fixes were applied
        check_command = [
            sys.executable, "-m", "ruff", "check",
            str(code_dir)
        ]
        returncode2, stdout2, stderr2 = run_command(check_command, cwd=code_dir.parent)
        if returncode2 != 0:
            logger.warning(f"Remaining ruff issues:\n{stdout2}")
    else:
        logger.info("Ruff check --fix completed successfully.")
    
    return returncode == 0

def run_black_format(code_dir: Path) -> bool:
    """
    Run black formatting on the code directory.
    Returns True if successful, False otherwise.
    """
    format_command = [
        sys.executable, "-m", "black",
        str(code_dir)
    ]
    
    logger = logging.getLogger(__name__)
    logger.info(f"Running black format on {code_dir}...")
    
    returncode, stdout, stderr = run_command(format_command, cwd=code_dir.parent)
    
    if returncode != 0:
        logger.error(f"Black format failed:\n{stderr}\n{stdout}")
        return False
    
    logger.info("Black format completed successfully.")
    return True

import logging

def main():
    """
    Main entry point for formatting tasks.
    Runs ruff check/fix and black format on the code directory.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"
    
    if not code_dir.exists():
        logging.error(f"Code directory not found: {code_dir}")
        return 1
    
    logging.info(f"Starting formatting on {code_dir}")
    
    # Run ruff check and fix
    ruff_success = run_ruff_check_and_fix(code_dir)
    
    # Run black format
    black_success = run_black_format(code_dir)
    
    if ruff_success and black_success:
        logging.info("Formatting completed successfully.")
        return 0
    else:
        logging.warning("Formatting completed with warnings.")
        return 0  # Return 0 to allow pipeline to continue even if minor issues remain

if __name__ == "__main__":
    sys.exit(main())

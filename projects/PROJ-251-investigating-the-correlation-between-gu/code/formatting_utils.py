import subprocess
import sys
import os
from pathlib import Path
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

def run_command(cmd: list, cwd: Path = None) -> Tuple[int, str, str]:
    """
    Run a shell command and return (returncode, stdout, stderr).
    
    Args:
        cmd: List of command arguments
        cwd: Working directory for the command
        
    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        logger.error(f"Command execution failed: {e}")
        return -1, "", str(e)

def run_ruff_check_and_fix(code_dir: Path) -> Tuple[bool, list]:
    """
    Run ruff check and fix on the code directory.
    
    Args:
        code_dir: Path to the code directory
        
    Returns:
        Tuple of (success, report_lines)
    """
    logger.info(f"Running ruff check and fix on {code_dir}")
    
    # Run ruff check first to see issues
    check_code, check_out, check_err = run_command(
        ["python", "-m", "ruff", "check", str(code_dir)],
        cwd=code_dir.parent
    )
    
    if check_code != 0:
        logger.info("Ruff found issues. Attempting to fix...")
        # Run ruff check --fix
        fix_code, fix_out, fix_err = run_command(
            ["python", "-m", "ruff", "check", "--fix", str(code_dir)],
            cwd=code_dir.parent
        )
        
        if fix_code != 0:
            logger.warning(f"Ruff fix returned non-zero: {fix_code}")
            logger.warning(f"stdout: {fix_out}")
            logger.warning(f"stderr: {fix_err}")
        else:
            logger.info("Ruff fix completed successfully")
    
    # Run ruff check again to verify
    final_code, final_out, final_err = run_command(
        ["python", "-m", "ruff", "check", str(code_dir)],
        cwd=code_dir.parent
    )
    
    success = (final_code == 0)
    report_lines = [
        f"Ruff check result: {'PASSED' if success else 'FAILED'}",
        f"Exit code: {final_code}",
        f"Output: {final_out}",
        f"Errors: {final_err}"
    ]
    
    return success, report_lines

def run_black_format(code_dir: Path) -> Tuple[bool, list]:
    """
    Run black format on the code directory.
    
    Args:
        code_dir: Path to the code directory
        
    Returns:
        Tuple of (success, report_lines)
    """
    logger.info(f"Running black format on {code_dir}")
    
    code, out, err = run_command(
        ["python", "-m", "black", str(code_dir)],
        cwd=code_dir.parent
    )
    
    success = (code == 0)
    report_lines = [
        f"Black format result: {'PASSED' if success else 'FAILED'}",
        f"Exit code: {code}",
        f"Output: {out}",
        f"Errors: {err}"
    ]
    
    return success, report_lines

def main():
    """Main entry point for formatting utilities demonstration."""
    print("Formatting utilities module. Use run_ruff_check_and_fix or run_black_format.")
    return 0

if __name__ == "__main__":
    sys.exit(main())

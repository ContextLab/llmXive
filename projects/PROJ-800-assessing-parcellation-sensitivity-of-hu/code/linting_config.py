"""
Linting and formatting configuration helpers for PROJ-800.
Provides command-line strings for ruff and black execution.
"""
import subprocess
from typing import List, Optional

from utils.logger import get_logger, ConfigurationError

logger = get_logger(__name__)

def get_ruff_command(check: bool = False, fix: bool = False, path: Optional[str] = None) -> List[str]:
    """
    Construct the ruff command line arguments.

    Args:
        check: If True, run in check-only mode (default).
        fix: If True, attempt to fix issues automatically.
        path: Optional specific file or directory to target. Defaults to current project root 'code'.

    Returns:
        List of command parts for subprocess execution.
    """
    cmd = ["ruff"]
    if fix:
        cmd.append("check")
        cmd.append("--fix")
    elif check:
        cmd.append("check")
    else:
        # Default behavior: check
        cmd.append("check")

    # Target path
    target = path if path else "code"
    cmd.append(target)

    logger.debug(f"Constructed ruff command: {' '.join(cmd)}")
    return cmd

def get_ruff_fix_command(path: Optional[str] = None) -> List[str]:
    """
    Construct the ruff command specifically for fixing issues.

    Args:
        path: Optional specific file or directory to target.

    Returns:
        List of command parts for subprocess execution.
    """
    return get_ruff_command(check=False, fix=True, path=path)

def get_black_command(check: bool = False, path: Optional[str] = None) -> List[str]:
    """
    Construct the black command line arguments.

    Args:
        check: If True, run in check-only mode (diff output).
        path: Optional specific file or directory to target. Defaults to 'code'.

    Returns:
        List of command parts for subprocess execution.
    """
    cmd = ["black"]
    if check:
        cmd.append("--check")
        cmd.append("--diff")

    target = path if path else "code"
    cmd.append(target)

    logger.debug(f"Constructed black command: {' '.join(cmd)}")
    return cmd

def get_black_check_command(path: Optional[str] = None) -> List[str]:
    """
    Construct the black command specifically for checking formatting (no write).

    Args:
        path: Optional specific file or directory to target.

    Returns:
        List of command parts for subprocess execution.
    """
    return get_black_command(check=True, path=path)

def run_linting_tools() -> int:
    """
    Execute ruff and black checks on the codebase.

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    logger.info("Starting linting and formatting checks...")

    ruff_cmd = get_ruff_command()
    black_cmd = get_black_command(check=True)

    try:
        logger.info(f"Running: {' '.join(ruff_cmd)}")
        ruff_result = subprocess.run(ruff_cmd, check=False)
        if ruff_result.returncode != 0:
            logger.error("Ruff check failed. Please fix linting errors.")
            return ruff_result.returncode

        logger.info(f"Running: {' '.join(black_cmd)}")
        black_result = subprocess.run(black_cmd, check=False)
        if black_result.returncode != 0:
            logger.error("Black check failed. Please run 'black code' to format.")
            return black_result.returncode

        logger.info("All linting and formatting checks passed.")
        return 0

    except FileNotFoundError as e:
        msg = "Linting tools (ruff or black) not found. Install them via 'pip install ruff black'."
        logger.error(msg)
        raise ConfigurationError(msg) from e

def run_linting_fix() -> int:
    """
    Execute ruff fix and black formatting on the codebase.

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    logger.info("Starting automatic fixes and formatting...")

    ruff_cmd = get_ruff_fix_command()
    black_cmd = get_black_command(check=False)

    try:
        logger.info(f"Running: {' '.join(ruff_cmd)}")
        ruff_result = subprocess.run(ruff_cmd, check=False)
        if ruff_result.returncode != 0:
            logger.warning("Ruff fix encountered issues (some may be unfixable).")

        logger.info(f"Running: {' '.join(black_cmd)}")
        black_result = subprocess.run(black_cmd, check=False)
        if black_result.returncode != 0:
            logger.error("Black formatting failed unexpectedly.")
            return black_result.returncode

        logger.info("Fixes and formatting applied.")
        return 0

    except FileNotFoundError as e:
        msg = "Linting tools (ruff or black) not found. Install them via 'pip install ruff black'."
        logger.error(msg)
        raise ConfigurationError(msg) from e

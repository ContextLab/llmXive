import subprocess
import sys
import os
from pathlib import Path
from typing import Tuple, Optional
import logging

from utils.logging_config import get_logger

logger = get_logger(__name__)

def run_command(cmd: list, cwd: Optional[Path] = None) -> Tuple[int, str, str]:
    """
    Run a shell command and return exit code, stdout, and stderr.

    Args:
        cmd: Command as a list of strings
        cwd: Working directory for the command

    Returns:
        Tuple of (exit_code, stdout, stderr)
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
        logger.error(f"Error running command: {cmd}")
        logger.error(f"Exception: {e}")
        return -1, "", str(e)

def run_ruff_check_and_fix(code_dir: Path) -> Tuple[int, str]:
    """
    Run ruff check and fix on the code directory.

    Args:
        code_dir: Path to the code directory

    Returns:
        Tuple of (exit_code, report_message)
    """
    logger.info(f"Running ruff check on {code_dir}")

    # First, run ruff check to see issues
    check_cmd = [sys.executable, "-m", "ruff", "check", str(code_dir), "--output-format=text"]
    exit_code, stdout, stderr = run_command(check_cmd, code_dir)

    report_lines = [f"RUFF CHECK RESULTS (Exit Code: {exit_code})"]
    report_lines.append("=" * 50)

    if stdout.strip():
        report_lines.append("Issues found:")
        report_lines.append(stdout)
    else:
        report_lines.append("No issues found (or no output).")

    if stderr.strip():
        report_lines.append("Errors/Warnings:")
        report_lines.append(stderr)

    # Now run ruff fix
    logger.info("Running ruff fix...")
    fix_cmd = [sys.executable, "-m", "ruff", "check", str(code_dir), "--fix", "--exit-zero"]
    exit_code_fix, stdout_fix, stderr_fix = run_command(fix_cmd, code_dir)

    report_lines.append("")
    report_lines.append(f"RUFF FIX RESULTS (Exit Code: {exit_code_fix})")
    report_lines.append("=" * 50)

    if stdout_fix.strip():
        report_lines.append("Fix report:")
        report_lines.append(stdout_fix)
    else:
        report_lines.append("No fixes needed or applied.")

    if stderr_fix.strip():
        report_lines.append("Fix errors/warnings:")
        report_lines.append(stderr_fix)

    report_message = "\n".join(report_lines)
    return exit_code_fix, report_message

def run_black_format(code_dir: Path) -> Tuple[int, str]:
    """
    Run black format on the code directory.

    Args:
        code_dir: Path to the code directory

    Returns:
        Tuple of (exit_code, report_message)
    """
    logger.info(f"Running black format on {code_dir}")

    cmd = [sys.executable, "-m", "black", "--check", str(code_dir)]
    exit_code_check, stdout_check, stderr_check = run_command(cmd, code_dir)

    report_lines = [f"BLACK CHECK RESULTS (Exit Code: {exit_code_check})"]
    report_lines.append("=" * 50)

    if stdout_check.strip():
        report_lines.append(stdout_check)
    if stderr_check.strip():
        report_lines.append(stderr_check)

    # If check failed, run black to format
    if exit_code_check != 0:
        logger.info("Formatting with black...")
        format_cmd = [sys.executable, "-m", "black", str(code_dir)]
        exit_code_format, stdout_format, stderr_format = run_command(format_cmd, code_dir)

        report_lines.append("")
        report_lines.append(f"BLACK FORMAT RESULTS (Exit Code: {exit_code_format})")
        report_lines.append("=" * 50)

        if stdout_format.strip():
            report_lines.append("Format report:")
            report_lines.append(stdout_format)
        if stderr_format.strip():
            report_lines.append("Format errors/warnings:")
            report_lines.append(stderr_format)

        return exit_code_format, "\n".join(report_lines)

    return exit_code_check, "\n".join(report_lines)

def main():
    """Main entry point for formatting utilities."""
    logger.info("Formatting utilities module loaded.")
    # This module is intended to be imported and used by other scripts
    return 0

if __name__ == "__main__":
    sys.exit(main())

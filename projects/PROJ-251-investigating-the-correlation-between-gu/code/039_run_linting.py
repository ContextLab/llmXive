"""
Task T039: Run ruff check and black format on all files in code/ and fix all reported issues.

This script executes ruff and black against the code/ directory, captures the output,
attempts to fix issues automatically, and writes a comprehensive lint report to
data/results/lint_report.txt.
"""
import os
import sys
import subprocess
import json
from pathlib import Path
import logging

# Add project root to path if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger

logger = get_logger(__name__)

def run_command(cmd: list, capture_output: bool = True) -> tuple:
    """
    Run a shell command and return (return_code, stdout, stderr).
    
    Args:
        cmd: Command as a list of strings
        capture_output: Whether to capture stdout/stderr
        
    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    logger.info(f"Running command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            timeout=300
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out: {' '.join(cmd)}")
        return -1, "", "Command timed out"
    except Exception as e:
        logger.error(f"Error running command: {e}")
        return -1, "", str(e)

def run_ruff_check_and_fix(code_dir: Path, report_path: Path) -> bool:
    """
    Run ruff check on code directory, attempt to fix issues, and return success status.
    
    Args:
        code_dir: Path to the code directory
        report_path: Path to the lint report file
        
    Returns:
        True if ruff completed successfully (exit code 0), False otherwise
    """
    logger.info("Starting Ruff check and fix...")
    
    # First, try to fix issues automatically
    fix_cmd = [sys.executable, "-m", "ruff", "check", str(code_dir), "--fix"]
    returncode, stdout, stderr = run_command(fix_cmd)
    
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("RUFF CHECK AND FIX REPORT")
    report_lines.append(f"Timestamp: {Path(report_path).parent.parent.name if report_path else 'N/A'}")
    report_lines.append("=" * 80)
    report_lines.append("")
    report_lines.append(f"Command: {' '.join(fix_cmd)}")
    report_lines.append(f"Exit Code: {returncode}")
    report_lines.append("")
    
    if stdout:
        report_lines.append("STDOUT:")
        report_lines.append("-" * 40)
        report_lines.append(stdout)
        report_lines.append("-" * 40)
        report_lines.append("")
    
    if stderr:
        report_lines.append("STDERR:")
        report_lines.append("-" * 40)
        report_lines.append(stderr)
        report_lines.append("-" * 40)
        report_lines.append("")
    
    # Run ruff check again to verify fixes
    check_cmd = [sys.executable, "-m", "ruff", "check", str(code_dir)]
    returncode_check, stdout_check, stderr_check = run_command(check_cmd)
    
    report_lines.append("VERIFICATION CHECK:")
    report_lines.append(f"Command: {' '.join(check_cmd)}")
    report_lines.append(f"Exit Code: {returncode_check}")
    
    if stdout_check:
        report_lines.append("STDOUT:")
        report_lines.append("-" * 40)
        report_lines.append(stdout_check)
        report_lines.append("-" * 40)
    
    if stderr_check:
        report_lines.append("STDERR:")
        report_lines.append("-" * 40)
        report_lines.append(stderr_check)
        report_lines.append("-" * 40)
    
    report_lines.append("")
    report_lines.append("=" * 80)
    report_lines.append(f"RUFF FINAL STATUS: {'PASSED' if returncode_check == 0 else 'FAILED'}")
    report_lines.append("=" * 80)
    
    # Write report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w') as f:
        f.write('\n'.join(report_lines))
    
    logger.info(f"Ruff report written to {report_path}")
    return returncode_check == 0

def run_black_format(code_dir: Path, report_path: Path) -> bool:
    """
    Run black format on code directory and return success status.
    
    Args:
        code_dir: Path to the code directory
        report_path: Path to the lint report file (appended to)
        
    Returns:
        True if black completed successfully (exit code 0), False otherwise
    """
    logger.info("Starting Black format...")
    
    # Run black with --check first to see what would change
    check_cmd = [sys.executable, "-m", "black", "--check", str(code_dir)]
    returncode_check, stdout_check, stderr_check = run_command(check_cmd)
    
    # Now run black to actually format
    format_cmd = [sys.executable, "-m", "black", str(code_dir)]
    returncode, stdout, stderr = run_command(format_cmd)
    
    # Read existing report and append
    report_lines = []
    if report_path.exists():
        with open(report_path, 'r') as f:
            report_lines = f.readlines()
        # Remove trailing newline if present
        if report_lines and report_lines[-1].strip() == '':
            report_lines = report_lines[:-1]
    else:
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("BLACK FORMAT REPORT")
        report_lines.append("=" * 80)
    
    report_lines.append("")
    report_lines.append("-" * 80)
    report_lines.append("BLACK FORMATTING")
    report_lines.append("-" * 80)
    report_lines.append("")
    report_lines.append(f"Format Command: {' '.join(format_cmd)}")
    report_lines.append(f"Format Exit Code: {returncode}")
    
    if stdout:
        report_lines.append("STDOUT:")
        report_lines.append("-" * 40)
        report_lines.append(stdout)
        report_lines.append("-" * 40)
    
    if stderr:
        report_lines.append("STDERR:")
        report_lines.append("-" * 40)
        report_lines.append(stderr)
        report_lines.append("-" * 40)
    
    report_lines.append("")
    report_lines.append(f"Black Final Status: {'PASSED' if returncode == 0 else 'FAILED'}")
    report_lines.append("=" * 80)
    
    # Write updated report
    with open(report_path, 'w') as f:
        f.write(''.join(report_lines))
    
    logger.info(f"Black report appended to {report_path}")
    return returncode == 0

def main():
    """
    Main entry point for T039: Run ruff and black on code/ directory.
    """
    logger.info("Starting T039: Linting and formatting")
    
    # Define paths
    code_dir = Path(__file__).resolve().parent
    project_root = code_dir.parent
    report_path = project_root / "data" / "results" / "lint_report.txt"
    
    # Ensure report directory exists
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if ruff and black are installed
    logger.info("Checking for ruff and black...")
    ruff_cmd = [sys.executable, "-m", "ruff", "--version"]
    black_cmd = [sys.executable, "-m", "black", "--version"]
    
    _, ruff_stdout, _ = run_command(ruff_cmd)
    _, black_stdout, _ = run_command(black_cmd)
    
    logger.info(f"Ruff: {ruff_stdout.strip()}")
    logger.info(f"Black: {black_stdout.strip()}")
    
    # Run ruff check and fix
    ruff_success = run_ruff_check_and_fix(code_dir, report_path)
    
    # Run black format
    black_success = run_black_format(code_dir, report_path)
    
    # Final status
    success = ruff_success and black_success
    
    # Append final summary to report
    with open(report_path, 'a') as f:
        f.write("\n")
        f.write("=" * 80)
        f.write("\nFINAL TASK STATUS\n")
        f.write("=" * 80)
        f.write(f"\nRuff: {'PASSED' if ruff_success else 'FAILED'}")
        f.write(f"\nBlack: {'PASSED' if black_success else 'FAILED'}")
        f.write(f"\nOverall: {'PASSED' if success else 'FAILED'}")
        f.write("\n")
        f.write("=" * 80)
    
    if success:
        logger.info("T039 completed successfully: All files linted and formatted")
        print(f"Lint report written to: {report_path}")
        return 0
    else:
        logger.error("T039 failed: Some linting/formatting issues could not be resolved")
        print(f"Lint report written to: {report_path}")
        print("Check the report for details on failures.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
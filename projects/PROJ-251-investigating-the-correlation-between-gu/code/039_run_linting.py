"""
Task T039: Run ruff check and black format on all files in code/ and fix all reported issues.

This script executes ruff and black on the codebase, fixes all issues, and writes a report
to data/results/lint_report.txt containing the exit codes and summary of actions.
"""
import os
import sys
import subprocess
import json
from pathlib import Path
import logging

# Add project root to path to ensure imports work if needed, though this script is self-contained
PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "code"
RESULTS_DIR = PROJECT_ROOT / "data" / "results"
LINT_REPORT_PATH = RESULTS_DIR / "lint_report.txt"

# Ensure results directory exists
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_command(cmd: list, description: str) -> tuple:
    """
    Execute a shell command and return (stdout, stderr, return_code).
    """
    logger.info(f"Running: {description}")
    logger.info(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False  # We handle non-zero exits manually
        )
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        logger.error(f"Exception running {description}: {e}")
        return "", str(e), -1

def run_ruff_check_and_fix() -> tuple:
    """
    Run ruff check with fix option.
    Returns (stdout, stderr, exit_code).
    """
    # First, run ruff check to see what issues exist
    cmd_check = [sys.executable, "-m", "ruff", "check", str(CODE_DIR)]
    stdout, stderr, code = run_command(cmd_check, "Ruff Check (Initial)")
    
    # Run ruff check with --fix to automatically fix issues
    cmd_fix = [sys.executable, "-m", "ruff", "check", str(CODE_DIR), "--fix"]
    stdout_fix, stderr_fix, code_fix = run_command(cmd_fix, "Ruff Check with --fix")
    
    # Run ruff check again to verify all issues are fixed
    cmd_verify = [sys.executable, "-m", "ruff", "check", str(CODE_DIR)]
    stdout_verify, stderr_verify, code_verify = run_command(cmd_verify, "Ruff Check (Verification)")
    
    # Combine outputs for the report
    full_output = (
        f"=== RUFF CHECK (Initial) ===\n{stdout}\n{stderr}\nExit Code: {code}\n\n"
        f"=== RUFF CHECK WITH FIX ===\n{stdout_fix}\n{stderr_fix}\nExit Code: {code_fix}\n\n"
        f"=== RUFF CHECK (Verification) ===\n{stdout_verify}\n{stderr_verify}\nExit Code: {code_verify}\n"
    )
    
    return full_output, "", code_verify

def run_black_format() -> tuple:
    """
    Run black formatter on code directory.
    Returns (stdout, stderr, exit_code).
    """
    cmd = [sys.executable, "-m", "black", str(CODE_DIR)]
    stdout, stderr, code = run_command(cmd, "Black Format")
    return stdout, stderr, code

def write_report(ruff_output: str, ruff_code: int, black_output: str, black_code: int):
    """
    Write the final lint report to data/results/lint_report.txt.
    """
    report_content = (
        f"Lint Report for Project: investigating-the-correlation-between-gu\n"
        f"Generated at: {Path.cwd()}\n"
        f"{'='*80}\n\n"
        
        f"RUFF CHECK RESULTS:\n"
        f"{'-'*40}\n"
        f"{ruff_output}\n"
        f"Ruff Final Exit Code: {ruff_code}\n\n"
        
        f"BLACK FORMAT RESULTS:\n"
        f"{'-'*40}\n"
        f"{black_output}\n"
        f"Black Exit Code: {black_code}\n\n"
        
        f"SUMMARY:\n"
        f"{'-'*40}\n"
        f"Ruff Status: {'SUCCESS' if ruff_code == 0 else 'FAILED'}\n"
        f"Black Status: {'SUCCESS' if black_code == 0 else 'FAILED'}\n"
        f"Overall Status: {'SUCCESS' if ruff_code == 0 and black_code == 0 else 'FAILED'}\n"
    )
    
    with open(LINT_REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    logger.info(f"Report written to: {LINT_REPORT_PATH}")

def main():
    """
    Main entry point for T039.
    """
    logger.info("Starting T039: Linting and Formatting")
    
    # Check if ruff and black are installed
    try:
        subprocess.run([sys.executable, "-m", "ruff", "--version"], check=True, capture_output=True)
        subprocess.run([sys.executable, "-m", "black", "--version"], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Required tools (ruff, black) are not installed or not in PATH: {e}")
        # We still proceed to let the commands fail naturally if tools are missing
    
    # Run Ruff
    ruff_stdout, ruff_stderr, ruff_code = run_ruff_check_and_fix()
    
    # Run Black
    black_stdout, black_stderr, black_code = run_black_format()
    
    # Write Report
    write_report(ruff_stdout, ruff_code, black_stdout, black_code)
    
    # Determine success
    if ruff_code == 0 and black_code == 0:
        logger.info("T039 completed successfully. All linting and formatting issues resolved.")
        sys.exit(0)
    else:
        logger.error(f"T039 failed. Ruff code: {ruff_code}, Black code: {black_code}. Check report at {LINT_REPORT_PATH}")
        sys.exit(1)

if __name__ == "__main__":
    main()

"""
Task T039: Run ruff check and black format on all files in code/ and fix all reported issues.
Generates a lint report at data/results/lint_report.txt.
"""
import os
import sys
import subprocess
import json
from pathlib import Path
import logging

# Add project root to path to allow imports if needed, though this script mostly calls CLI
project_root = Path(__file__).resolve().parent.parent
code_dir = project_root / "code"
results_dir = project_root / "data" / "results"
report_path = results_dir / "lint_report.txt"

# Ensure results directory exists
results_dir.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(results_dir / "linting_execution.log")
    ]
)
logger = logging.getLogger(__name__)

def run_command(cmd: list, description: str) -> tuple:
    """
    Runs a shell command and returns (success, output, error).
    """
    logger.info(f"Running: {description}")
    logger.info(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False  # We handle non-zero exit codes manually
        )
        
        success = result.returncode == 0
        output = result.stdout
        error = result.stderr
        
        if output:
            logger.info(f"Output:\n{output}")
        if error:
            logger.warning(f"Error/Stderr:\n{error}")
        
        return success, output, error
    
    except FileNotFoundError:
        logger.error(f"Command not found: {cmd[0]}. Please install ruff and black.")
        return False, "", f"Command not found: {cmd[0]}"
    except Exception as e:
        logger.error(f"Exception running command: {e}")
        return False, "", str(e)

def main():
    logger.info("Starting T039: Linting and Formatting")
    
    # Check if code directory exists
    if not code_dir.exists():
        logger.error(f"Code directory not found: {code_dir}")
        # Write failure report
        with open(report_path, 'w') as f:
            f.write("Linting Failed: Code directory not found.\n")
            f.write(f"Path: {code_dir}\n")
        return 1

    # 1. Run Ruff Check (Fix)
    # We run ruff check with --fix to automatically fix fixable issues
    # and then run it again to see if any remain.
    ruff_cmd = [sys.executable, "-m", "ruff", "check", str(code_dir), "--fix"]
    success_ruff_fix, out_ruff_fix, err_ruff_fix = run_command(ruff_cmd, "Ruff Check (Fix)")
    
    # Run ruff check again to see if there are remaining issues
    ruff_check_cmd = [sys.executable, "-m", "ruff", "check", str(code_dir)]
    success_ruff_check, out_ruff_check, err_ruff_check = run_command(ruff_check_cmd, "Ruff Check (Verify)")

    ruff_success = success_ruff_check
    ruff_output = out_ruff_check if out_ruff_check else (out_ruff_fix if out_ruff_fix else "No issues found after fix.")
    
    # 2. Run Black Format
    black_cmd = [sys.executable, "-m", "black", str(code_dir)]
    success_black, out_black, err_black = run_command(black_cmd, "Black Format")
    
    black_output = out_black if out_black else (err_black if err_black else "No changes needed.")

    # 3. Generate Report
    # The task requires the report to contain the exit code (0) and a summary.
    # If either ruff or black failed (returned non-zero), the task fails.
    overall_success = ruff_success and success_black
    exit_code = 0 if overall_success else 1

    report_lines = [
        f"T039 Linting Report",
        f"==================",
        f"Timestamp: {Path(report_path).stat().st_mtime}",
        f"Code Directory: {code_dir}",
        f"",
        f"Overall Status: {'SUCCESS' if overall_success else 'FAILED'}",
        f"Exit Code: {exit_code}",
        f"",
        f"--- Ruff Results ---",
        f"Status: {'PASS' if ruff_success else 'FAIL'}",
        f"Output:\n{ruff_output}",
        f"",
        f"--- Black Results ---",
        f"Status: {'PASS' if success_black else 'FAIL'}",
        f"Output:\n{black_output}",
        f"",
    ]

    if not overall_success:
        report_lines.append("ERROR: Linting or formatting failed. Please review the output above.")
    
    report_content = "\n".join(report_lines)
    
    # Write report
    with open(report_path, 'w') as f:
        f.write(report_content)
    
    logger.info(f"Report written to: {report_path}")
    
    if overall_success:
        logger.info("T039 Completed Successfully.")
        return 0
    else:
        logger.error("T039 Failed: Ruff or Black reported errors.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

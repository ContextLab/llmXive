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
    Execute a shell command and return (exit_code, stdout, stderr).
    """
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            timeout=300
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out: {' '.join(cmd)}")
        return -1, "", "Command timed out"
    except Exception as e:
        logger.error(f"Error executing command: {e}")
        return -1, "", str(e)

def run_ruff_check_and_fix(code_dir: Path) -> Tuple[int, str]:
    """
    Run ruff check and fix on the code directory.
    Returns (exit_code, summary_message).
    """
    logger.info(f"Running ruff check on {code_dir}...")
    
    # First run check to see issues
    check_code, check_stdout, check_stderr = run_command(
        [sys.executable, "-m", "ruff", "check", str(code_dir)],
        cwd=code_dir.parent
    )
    
    issues_found = []
    if check_stdout:
        issues_found.append("Ruff Check Output:\n" + check_stdout)
    if check_stderr:
        issues_found.append("Ruff Check Errors:\n" + check_stderr)
    
    # Run fix
    logger.info("Running ruff fix...")
    fix_code, fix_stdout, fix_stderr = run_command(
        [sys.executable, "-m", "ruff", "check", str(code_dir), "--fix"],
        cwd=code_dir.parent
    )
    
    if fix_stdout:
        issues_found.append("Ruff Fix Output:\n" + fix_stdout)
    
    summary = "\n".join(issues_found) if issues_found else "No issues found."
    return fix_code, summary

def run_black_format(code_dir: Path) -> Tuple[int, str]:
    """
    Run black format on the code directory.
    Returns (exit_code, summary_message).
    """
    logger.info(f"Running black format on {code_dir}...")
    
    code, stdout, stderr = run_command(
        [sys.executable, "-m", "black", str(code_dir)],
        cwd=code_dir.parent
    )
    
    summary_parts = []
    if stdout:
        summary_parts.append("Black Output:\n" + stdout)
    if stderr:
        summary_parts.append("Black Errors:\n" + stderr)
    
    summary = "\n".join(summary_parts) if summary_parts else "Formatting complete."
    return code, summary

def main():
    """
    Main entry point for formatting tasks.
    Runs ruff and black on the code/ directory and generates a report.
    """
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"
    results_dir = project_root / "data" / "results"
    
    # Ensure results directory exists
    results_dir.mkdir(parents=True, exist_ok=True)
    report_path = results_dir / "lint_report.txt"
    
    logger.info(f"Starting linting and formatting for project at {project_root}")
    
    all_output = []
    all_output.append(f"Linting Report for {code_dir}")
    all_output.append("=" * 50)
    
    # Run Ruff
    ruff_code, ruff_summary = run_ruff_check_and_fix(code_dir)
    all_output.append(f"\nRuff Exit Code: {ruff_code}")
    all_output.append(ruff_summary)
    
    # Run Black
    black_code, black_summary = run_black_format(code_dir)
    all_output.append(f"\nBlack Exit Code: {black_code}")
    all_output.append(black_summary)
    
    # Determine overall success
    overall_success = (ruff_code == 0) and (black_code == 0)
    all_output.append(f"\nOverall Status: {'SUCCESS' if overall_success else 'ISSUES FOUND'}")
    
    # Write report
    report_content = "\n".join(all_output)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    
    logger.info(f"Lint report written to {report_path}")
    
    if not overall_success:
        logger.warning("Linting or formatting reported issues. Check report for details.")
    
    return 0 if overall_success else 1

if __name__ == "__main__":
    sys.exit(main())

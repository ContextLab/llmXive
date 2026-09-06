"""
Task T039: Run ruff check and black format on all files in code/ and fix all reported issues.

This script executes ruff and black against the codebase, fixes issues automatically,
and generates a lint report.
"""
import os
import sys
import subprocess
import json
from pathlib import Path
import logging
from utils.logging_config import get_logger

def run_command(cmd: list, cwd: Path = None) -> tuple:
    """
    Run a shell command and return (exit_code, stdout, stderr).
    
    Args:
        cmd: Command and arguments as a list.
        cwd: Working directory for the command.
        
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
        logging.error(f"Error running command: {cmd}")
        logging.error(str(e))
        return -1, "", str(e)

def main():
    """
    Main entry point for T039.
    
    1. Runs `ruff check code/ --fix` to fix linting issues.
    2. Runs `black code/` to format code.
    3. Runs `ruff check code/` again to verify clean state.
    4. Writes `data/results/lint_report.txt` with the results.
    """
    logger = get_logger("T039_Linting")
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"
    results_dir = project_root / "data" / "results"
    report_path = results_dir / "lint_report.txt"

    # Ensure results directory exists
    results_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting linting and formatting for {code_dir}")
    
    report_lines = [
        f"T039 Linting Report - {Path(__file__).name}",
        f"Timestamp: {Path(__file__).stat().st_mtime}",
        f"Target Directory: {code_dir}",
        "=" * 60,
        ""
    ]

    # Step 1: Run Ruff Check with Fix
    logger.info("Step 1: Running ruff check --fix...")
    ruff_fix_cmd = [
        sys.executable, "-m", "ruff", "check", 
        str(code_dir), 
        "--fix",
        "--exit-zero" # Don't fail if fixes were made
    ]
    exit_code, stdout, stderr = run_command(ruff_fix_cmd)
    
    report_lines.append(f"Command: {' '.join(ruff_fix_cmd)}")
    report_lines.append(f"Exit Code: {exit_code}")
    if stdout:
        report_lines.append(f"Output:\n{stdout}")
    if stderr:
        report_lines.append(f"Errors:\n{stderr}")
    report_lines.append("-" * 60)

    # Step 2: Run Black Format
    logger.info("Step 2: Running black...")
    black_cmd = [
        sys.executable, "-m", "black", 
        str(code_dir)
    ]
    exit_code, stdout, stderr = run_command(black_cmd)
    
    report_lines.append(f"Command: {' '.join(black_cmd)}")
    report_lines.append(f"Exit Code: {exit_code}")
    if stdout:
        report_lines.append(f"Output:\n{stdout}")
    if stderr:
        report_lines.append(f"Errors:\n{stderr}")
    report_lines.append("-" * 60)

    # Step 3: Verify Clean State (Ruff Check without fix)
    logger.info("Step 3: Verifying clean state with ruff check...")
    ruff_verify_cmd = [
        sys.executable, "-m", "ruff", "check", 
        str(code_dir)
    ]
    exit_code, stdout, stderr = run_command(ruff_verify_cmd)
    
    report_lines.append(f"Command: {' '.join(ruff_verify_cmd)}")
    report_lines.append(f"Exit Code: {exit_code}")
    if stdout:
        report_lines.append(f"Output:\n{stdout}")
    if stderr:
        report_lines.append(f"Errors:\n{stderr}")
    
    # Final Summary
    report_lines.append("=" * 60)
    if exit_code == 0:
        report_lines.append("STATUS: SUCCESS - All files are linted and formatted.")
        final_status = "success"
    else:
        report_lines.append("STATUS: FAILED - Linting errors remain or formatting failed.")
        final_status = "failed"
    
    report_lines.append(f"Final Exit Code: {exit_code}")
    
    # Write Report
    report_content = "\n".join(report_lines)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    
    logger.info(f"Lint report written to: {report_path}")
    
    # Exit with the verification exit code
    sys.exit(exit_code)

if __name__ == "__main__":
    main()

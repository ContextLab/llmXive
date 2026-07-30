import os
import sys
import subprocess
import json
import logging
from pathlib import Path

from utils.logging_config import get_logger

# Ensure we can import sibling modules
sys.path.insert(0, str(Path(__file__).parent))

logger = get_logger(__name__)

def run_command(cmd: list, cwd: Path = None) -> tuple:
    """Run a shell command and return (returncode, stdout, stderr)."""
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

def run_ruff_check_and_fix(code_dir: Path) -> tuple:
    """Run ruff check and fix on the code directory. Returns (success, report_lines)."""
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

def run_black_format(code_dir: Path) -> tuple:
    """Run black format on the code directory. Returns (success, report_lines)."""
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
    """Main entry point for the formatting task."""
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"
    results_dir = project_root / "data" / "results"
    
    # Ensure results directory exists
    results_dir.mkdir(parents=True, exist_ok=True)
    
    report_path = results_dir / "lint_report.txt"
    
    logger.info(f"Starting formatting task. Code dir: {code_dir}")
    
    if not code_dir.exists():
        logger.error(f"Code directory does not exist: {code_dir}")
        with open(report_path, 'w') as f:
            f.write("ERROR: Code directory does not exist\n")
        return 1
    
    # Run ruff
    ruff_success, ruff_report = run_ruff_check_and_fix(code_dir)
    
    # Run black
    black_success, black_report = run_black_format(code_dir)
    
    # Write comprehensive report
    report_content = [
        "=" * 60,
        "LINTING AND FORMATTING REPORT",
        "=" * 60,
        "",
        f"Timestamp: {Path(report_path).parent.parent.name}",
        "",
        "--- RUFF CHECK ---",
    ] + ruff_report + [
        "",
        "--- BLACK FORMAT ---",
    ] + black_report + [
        "",
        "=" * 60,
        "SUMMARY",
        "=" * 60,
        f"Ruff check: {'PASSED' if ruff_success else 'FAILED'}",
        f"Black format: {'PASSED' if black_success else 'FAILED'}",
        f"Overall status: {'SUCCESS' if (ruff_success and black_success) else 'FAILED'}",
        "",
    ]
    
    report_text = "\n".join(report_content)
    
    with open(report_path, 'w') as f:
        f.write(report_text)
    
    logger.info(f"Report written to {report_path}")
    
    if ruff_success and black_success:
        logger.info("All formatting checks passed.")
        return 0
    else:
        logger.error("Formatting checks failed. Please review the report.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

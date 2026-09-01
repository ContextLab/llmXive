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

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_command(cmd: list, check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    logger.info(f"Running command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            check=check,
            capture_output=True,
            text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with exit code {e.returncode}")
        logger.error(f"stdout: {e.stdout}")
        logger.error(f"stderr: {e.stderr}")
        raise

def main():
    """Execute ruff check and black format, then generate report."""
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"
    results_dir = project_root / "data" / "results"
    report_path = results_dir / "lint_report.txt"

    # Ensure results directory exists
    results_dir.mkdir(parents=True, exist_ok=True)

    report_lines = []
    report_lines.append(f"Linting Report for {code_dir}")
    report_lines.append("=" * 50)
    report_lines.append("")

    # Step 1: Run ruff check (with fixes)
    logger.info("Running ruff check with fix...")
    try:
        ruff_result = run_command(
            [sys.executable, "-m", "ruff", "check", str(code_dir), "--fix"],
            check=False  # Don't fail immediately, we want to capture output
        )
        ruff_exit_code = ruff_result.returncode
        ruff_output = ruff_result.stdout + ruff_result.stderr

        report_lines.append("RUFF CHECK:")
        report_lines.append(f"Exit Code: {ruff_exit_code}")
        if ruff_output.strip():
            report_lines.append("Output:")
            report_lines.append(ruff_output)
        report_lines.append("")

        if ruff_exit_code != 0:
            # If ruff still has issues after fix, we might need to check if they are fixable
            # For now, we log the exit code. If it's non-zero, it means there are remaining issues.
            logger.warning(f"Ruff check found issues that could not be automatically fixed (Exit Code: {ruff_exit_code})")
    except Exception as e:
        report_lines.append(f"RUFF CHECK ERROR: {str(e)}")
        ruff_exit_code = 1

    # Step 2: Run black format
    logger.info("Running black format...")
    try:
        black_result = run_command(
            [sys.executable, "-m", "black", str(code_dir)],
            check=False
        )
        black_exit_code = black_result.returncode
        black_output = black_result.stdout + black_result.stderr

        report_lines.append("BLACK FORMAT:")
        report_lines.append(f"Exit Code: {black_exit_code}")
        if black_output.strip():
            report_lines.append("Output:")
            report_lines.append(black_output)
        report_lines.append("")
    except Exception as e:
        report_lines.append(f"BLACK FORMAT ERROR: {str(e)}")
        black_exit_code = 1

    # Summary
    report_lines.append("SUMMARY:")
    report_lines.append(f"Ruff Exit Code: {ruff_exit_code}")
    report_lines.append(f"Black Exit Code: {black_exit_code}")

    if ruff_exit_code == 0 and black_exit_code == 0:
        report_lines.append("Status: SUCCESS - All files linted and formatted.")
        final_status = 0
    else:
        report_lines.append("Status: ISSUES FOUND - Please review the output above.")
        final_status = 1

    report_lines.append("")
    report_lines.append("=" * 50)

    # Write report
    report_content = "\n".join(report_lines)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    logger.info(f"Lint report written to {report_path}")

    # Exit with appropriate code
    sys.exit(final_status)

if __name__ == "__main__":
    main()

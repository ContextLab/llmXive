import os
import sys
import subprocess
import json
import logging
from pathlib import Path

from utils.logging_config import get_logger
from formatting_utils import run_ruff_check_and_fix, run_black_format

logger = get_logger(__name__)

def main():
    """
    Run ruff and black on the code directory and generate a lint report.
    """
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"
    output_dir = project_root / "data" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)

    report_path = output_dir / "lint_report.txt"
    logger.info(f"Starting linting and formatting for {code_dir}")

    all_reports = []
    exit_codes = []

    # Run ruff
    logger.info("Running ruff...")
    ruff_exit, ruff_report = run_ruff_check_and_fix(code_dir)
    exit_codes.append(ruff_exit)
    all_reports.append(f"### RUFF CHECK AND FIX ###\n{ruff_report}\n")
    logger.info(f"Ruff completed with exit code: {ruff_exit}")

    # Run black
    logger.info("Running black...")
    black_exit, black_report = run_black_format(code_dir)
    exit_codes.append(black_exit)
    all_reports.append(f"### BLACK FORMAT ###\n{black_report}\n")
    logger.info(f"Black completed with exit code: {black_exit}")

    # Generate summary
    summary_lines = [
        "LINTING AND FORMATTING REPORT",
        "=" * 50,
        "",
        f"Code directory: {code_dir}",
        f"Ruff exit code: {ruff_exit}",
        f"Black exit code: {black_exit}",
        "",
    ]

    if ruff_exit == 0 and black_exit == 0:
        summary_lines.append("STATUS: SUCCESS - All checks passed and formatting applied.")
    else:
        summary_lines.append("STATUS: ISSUES FOUND - Please review the reports below.")

    summary_lines.append("")
    summary_lines.extend(all_reports)

    report_content = "\n".join(summary_lines)

    # Write report
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    logger.info(f"Lint report written to {report_path}")

    # Return success only if both exit codes are 0
    if ruff_exit == 0 and black_exit == 0:
        logger.info("All linting and formatting tasks completed successfully.")
        return 0
    else:
        logger.warning("Some linting or formatting tasks failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

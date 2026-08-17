import os
import sys
import subprocess
import json
import logging
from pathlib import Path

from code.formatting_utils import run_command, run_ruff_check_and_fix, run_black_format

logger = logging.getLogger(__name__)

def main():
    """
    Run ruff check and black format on all files in code/
    and generate a lint report.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"
    results_dir = project_root / "data" / "results"
    
    # Ensure results directory exists
    results_dir.mkdir(parents=True, exist_ok=True)
    lint_report_path = results_dir / "lint_report.txt"
    
    logger.info(f"Project root: {project_root}")
    logger.info(f"Code directory: {code_dir}")
    
    if not code_dir.exists():
        logger.error(f"Code directory does not exist: {code_dir}")
        with open(lint_report_path, 'w') as f:
            f.write(f"ERROR: Code directory does not exist: {code_dir}\n")
            f.write("Exit code: 1\n")
        return 1
    
    report_lines = []
    report_lines.append(f"Linting Report - {code_dir}")
    report_lines.append("=" * 50)
    
    # Run ruff check and fix
    logger.info("Running ruff check and fix...")
    ruff_code, ruff_out, ruff_err = run_ruff_check_and_fix(code_dir)
    report_lines.append(f"\nRuff Check/Fix:")
    report_lines.append(f"  Exit code: {ruff_code}")
    if ruff_out:
        report_lines.append(f"  Output:\n{ruff_out}")
    if ruff_err:
        report_lines.append(f"  Errors:\n{ruff_err}")
    
    # Run black format
    logger.info("Running black format...")
    black_code, black_out, black_err = run_black_format(code_dir)
    report_lines.append(f"\nBlack Format:")
    report_lines.append(f"  Exit code: {black_code}")
    if black_out:
        report_lines.append(f"  Output:\n{black_out}")
    if black_err:
        report_lines.append(f"  Errors:\n{black_err}")
    
    # Determine overall success
    overall_success = (ruff_code == 0 and black_code == 0)
    report_lines.append("\n" + "=" * 50)
    if overall_success:
        report_lines.append("STATUS: SUCCESS - All files are properly formatted and linted.")
        final_exit_code = 0
    else:
        report_lines.append("STATUS: FAILURE - Some files failed formatting or linting.")
        final_exit_code = 1
    
    report_lines.append(f"Final Exit Code: {final_exit_code}")
    
    # Write report
    report_content = "\n".join(report_lines)
    with open(lint_report_path, 'w') as f:
        f.write(report_content)
    
    logger.info(f"Lint report written to: {lint_report_path}")
    print(report_content)
    
    return final_exit_code

if __name__ == "__main__":
    sys.exit(main())
import os
import sys
import subprocess
import json
from pathlib import Path
import logging

from utils.logging_config import get_logger

def run_command(cmd: list, cwd: Path = None) -> tuple:
    """
    Executes a shell command and returns (stdout, stderr, returncode).
    """
    logger = get_logger("linting")
    logger.info(f"Running command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False
        )
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        logger.error(f"Error executing command: {e}")
        return "", str(e), 1

def run_ruff_check_and_fix(code_root: Path) -> tuple:
    """
    Runs ruff check on the code directory, attempts to fix issues,
    and returns the report content and exit code.
    """
    logger = get_logger("linting")
    report_lines = []
    report_lines.append("--- RUFF CHECK ---")

    # 1. Initial check (dry run) to see what needs fixing
    cmd_check = [sys.executable, "-m", "ruff", "check", str(code_root)]
    out, err, code = run_command(cmd_check, code_root)
    report_lines.append(out)
    report_lines.append(err)
    report_lines.append(f"Initial Check Exit Code: {code}")

    if code != 0:
        logger.info("Ruff found issues. Attempting to fix...")
        # 2. Fix attempt
        cmd_fix = [sys.executable, "-m", "ruff", "fix", str(code_root)]
        out_fix, err_fix, code_fix = run_command(cmd_fix, code_root)
        report_lines.append("--- RUFF FIX ---")
        report_lines.append(out_fix)
        report_lines.append(err_fix)
        report_lines.append(f"Fix Exit Code: {code_fix}")

        # 3. Re-check to ensure all issues are resolved
        cmd_final = [sys.executable, "-m", "ruff", "check", str(code_root)]
        out_final, err_final, code_final = run_command(cmd_final, code_root)
        report_lines.append("--- RUFF FINAL CHECK ---")
        report_lines.append(out_final)
        report_lines.append(err_final)
        report_lines.append(f"Final Check Exit Code: {code_final}")

        return "\n".join(report_lines), code_final
    else:
        return "\n".join(report_lines), 0

def run_black_format(code_root: Path) -> tuple:
    """
    Runs black format on the code directory and returns the report content and exit code.
    """
    logger = get_logger("linting")
    report_lines = []
    report_lines.append("--- BLACK FORMAT ---")

    cmd_check = [sys.executable, "-m", "black", "--check", str(code_root)]
    out, err, code = run_command(cmd_check, code_root)
    report_lines.append(out)
    report_lines.append(err)
    report_lines.append(f"Black Check Exit Code: {code}")

    if code != 0:
        logger.info("Black found formatting issues. Attempting to format...")
        cmd_format = [sys.executable, "-m", "black", str(code_root)]
        out_fmt, err_fmt, code_fmt = run_command(cmd_format, code_root)
        report_lines.append("--- BLACK FORMAT APPLIED ---")
        report_lines.append(out_fmt)
        report_lines.append(err_fmt)
        report_lines.append(f"Format Exit Code: {code_fmt}")

        # Re-check to ensure formatting is correct
        cmd_final = [sys.executable, "-m", "black", "--check", str(code_root)]
        out_final, err_final, code_final = run_command(cmd_final, code_root)
        report_lines.append("--- BLACK FINAL CHECK ---")
        report_lines.append(out_final)
        report_lines.append(err_final)
        report_lines.append(f"Final Check Exit Code: {code_final}")

        return "\n".join(report_lines), code_final
    else:
        return "\n".join(report_lines), 0

def main():
    logger = get_logger("linting")
    logger.info("Starting linting and formatting process for T039")

    # Determine project root
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent

    code_dir = project_root / "code"

    if not code_dir.exists():
        logger.error(f"Code directory not found: {code_dir}")
        sys.exit(1)

    # Run Ruff
    ruff_report, ruff_code = run_ruff_check_and_fix(code_dir)

    # Run Black
    black_report, black_code = run_black_format(code_dir)

    # Compile full report
    full_report = f"{ruff_report}\n\n{black_report}"

    # Save report
    results_dir = project_root / "data" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    report_path = results_dir / "lint_report.txt"

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(full_report)

    logger.info(f"Lint report saved to: {report_path}")

    # Determine success: Both ruff and black must exit with 0 after fixes
    if ruff_code == 0 and black_code == 0:
        logger.info("Linting and formatting completed successfully.")
        sys.exit(0)
    else:
        logger.error(f"Linting or formatting failed. Ruff: {ruff_code}, Black: {black_code}")
        sys.exit(1)

if __name__ == "__main__":
    main()

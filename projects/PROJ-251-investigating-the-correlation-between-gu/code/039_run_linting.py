import os
import sys
import subprocess
import json
from pathlib import Path
import logging

def run_command(cmd, cwd=None):
    """Execute a shell command and return the output and exit code."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False
        )
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), 1

def run_ruff_check_and_fix(code_dir):
    """Run ruff check with automatic fixes on the code directory."""
    logging.info("Running ruff check with fixes...")
    # First pass: check and fix automatically
    cmd_fix = f"ruff check {code_dir} --fix --exit-zero"
    stdout, stderr, code = run_command(cmd_fix, cwd=code_dir.parent)
    
    output_lines = []
    output_lines.append("=== RUFF CHECK (FIX MODE) ===")
    if stdout:
        output_lines.append(stdout)
    if stderr:
        output_lines.append(stderr)
    output_lines.append(f"Ruff Fix Exit Code: {code}")
    output_lines.append("")

    # Second pass: check for remaining issues (should be 0 if all fixed)
    logging.info("Running ruff check (final verification)...")
    cmd_check = f"ruff check {code_dir}"
    stdout, stderr, code = run_command(cmd_check, cwd=code_dir.parent)
    
    output_lines.append("=== RUFF CHECK (FINAL) ===")
    if stdout:
        output_lines.append(stdout)
    if stderr:
        output_lines.append(stderr)
    output_lines.append(f"Ruff Final Exit Code: {code}")
    output_lines.append("")
    
    return "\n".join(output_lines), code

def run_black_format(code_dir):
    """Run black formatter on the code directory."""
    logging.info("Running black format...")
    cmd = f"black {code_dir}"
    stdout, stderr, code = run_command(cmd, cwd=code_dir.parent)
    
    output_lines = []
    output_lines.append("=== BLACK FORMAT ===")
    if stdout:
        output_lines.append(stdout)
    if stderr:
        output_lines.append(stderr)
    output_lines.append(f"Black Exit Code: {code}")
    output_lines.append("")
    
    return "\n".join(output_lines), code

def write_report(report_content, output_path):
    """Write the linting report to a file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    logging.info(f"Report written to {output_path}")

def main():
    """Main entry point for the linting task."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    logger.info("Starting linting task (T039)...")

    # Determine paths
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"
    results_dir = project_root / "data" / "results"
    report_path = results_dir / "lint_report.txt"

    if not code_dir.exists():
        logger.error(f"Code directory not found: {code_dir}")
        sys.exit(1)

    report_parts = []
    report_parts.append(f"# Linting Report for {code_dir}")
    report_parts.append(f"Generated: {Path.cwd()}")
    report_parts.append("")

    # Run Ruff
    ruff_output, ruff_code = run_ruff_check_and_fix(code_dir)
    report_parts.append(ruff_output)

    # Run Black
    black_output, black_code = run_black_format(code_dir)
    report_parts.append(black_output)

    # Summary
    report_parts.append("=== SUMMARY ===")
    ruff_status = "PASSED" if ruff_code == 0 else "FAILED"
    black_status = "PASSED" if black_code == 0 else "FAILED"
    report_parts.append(f"Ruff: {ruff_status} (Exit Code: {ruff_code})")
    report_parts.append(f"Black: {black_status} (Exit Code: {black_code})")
    
    total_code = ruff_code + black_code
    report_parts.append(f"Overall Status: {'PASSED' if total_code == 0 else 'FAILED'}")
    
    final_report = "\n".join(report_parts)
    
    write_report(final_report, report_path)

    if total_code != 0:
        logger.warning(f"Linting reported issues (Exit Code: {total_code}). See {report_path} for details.")
        # In a strict CI environment, we might exit 1, but for this task 
        # we report the status. If the user wants strict failure, they can check the file.
        # However, the task description says "If exit code != 0, the task fails."
        # So we exit 1 if there are issues remaining after fixes.
        sys.exit(total_code)
    
    logger.info("Linting completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()

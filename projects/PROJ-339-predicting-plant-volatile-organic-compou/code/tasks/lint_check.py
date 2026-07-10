"""
Task T035: Run ruff and black checks on the codebase and save the report.

This script executes `ruff check` and `black --check` on the `code/` directory
and saves the combined output to `data/results/lint_report.txt`.
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd: list[str]) -> tuple[int, str, str]:
    """Run a shell command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            cwd=Path(__file__).parent.parent
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return -1, "", f"Error: Command '{cmd[0]}' not found. Please install dependencies."

def main():
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"
    results_dir = project_root / "data" / "results"
    
    # Ensure results directory exists
    results_dir.mkdir(parents=True, exist_ok=True)
    report_path = results_dir / "lint_report.txt"

    report_lines = []
    report_lines.append(f"Lint Report Generated: {Path(__file__).stem}")
    report_lines.append("=" * 60)
    report_lines.append("")

    # Check for ruff
    report_lines.append("1. Running 'ruff check code/'...")
    report_lines.append("-" * 40)
    ruff_code, ruff_out, ruff_err = run_command(["ruff", "check", "code/"])
    
    if ruff_code == -1:
        report_lines.append(ruff_err)
        report_lines.append("Skipping ruff check (command not found).")
    else:
        if ruff_out:
            report_lines.append(ruff_out)
        if ruff_err:
            report_lines.append(ruff_err)
        if ruff_code != 0:
            report_lines.append("Status: FAILED")
        else:
            report_lines.append("Status: PASSED")
    
    report_lines.append("")

    # Check for black
    report_lines.append("2. Running 'black --check code/'...")
    report_lines.append("-" * 40)
    black_code, black_out, black_err = run_command(["black", "--check", "code/"])

    if black_code == -1:
        report_lines.append(black_err)
        report_lines.append("Skipping black check (command not found).")
    else:
        if black_out:
            report_lines.append(black_out)
        if black_err:
            report_lines.append(black_err)
        if black_code != 0:
            report_lines.append("Status: FAILED")
        else:
            report_lines.append("Status: PASSED")

    report_lines.append("")
    report_lines.append("=" * 60)
    
    # Determine overall status
    if ruff_code == 0 and black_code == 0:
        overall_status = "OVERALL: PASSED"
    elif ruff_code == -1 or black_code == -1:
        overall_status = "OVERALL: SKIPPED (Missing tools)"
    else:
        overall_status = "OVERALL: FAILED"
    
    report_lines.append(overall_status)

    # Write to file
    full_report = "\n".join(report_lines)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(full_report)

    print(f"Lint report saved to: {report_path}")
    print(full_report)
    
    # Exit with non-zero if checks failed (optional, but good practice)
    if ruff_code != 0 and ruff_code != -1:
        sys.exit(1)
    if black_code != 0 and black_code != -1:
        sys.exit(1)

if __name__ == "__main__":
    main()
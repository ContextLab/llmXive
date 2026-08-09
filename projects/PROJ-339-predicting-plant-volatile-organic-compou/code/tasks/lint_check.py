import subprocess
import sys
import os
from pathlib import Path


def run_command(command: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    """
    Run a shell command and return (returncode, stdout, stderr).
    """
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 127, "", f"Command not found: {command[0]}"
    except Exception as e:
        return 1, "", str(e)


def main() -> None:
    """
    Run ruff check and black --check on the code/ directory.
    Save the combined output to data/results/lint_report.txt.
    """
    root = Path(__file__).resolve().parents[2]
    code_dir = root / "code"
    results_dir = root / "data" / "results"
    output_file = results_dir / "lint_report.txt"

    # Ensure output directory exists
    results_dir.mkdir(parents=True, exist_ok=True)

    report_lines = [
        "LINTING REPORT",
        f"Generated: {Path.cwd()}",
        "=" * 60,
        "",
    ]

    # 1. Run ruff check
    report_lines.append(">>> RUNNING: ruff check code/")
    report_lines.append("-" * 40)
    returncode_ruff, stdout_ruff, stderr_ruff = run_command(
        ["ruff", "check", str(code_dir)], cwd=root
    )
    if stdout_ruff:
        report_lines.append(stdout_ruff)
    if stderr_ruff:
        report_lines.append("STDERR:")
        report_lines.append(stderr_ruff)
    report_lines.append(f"Return code: {returncode_ruff}")
    report_lines.append("")

    # 2. Run black --check
    report_lines.append(">>> RUNNING: black --check code/")
    report_lines.append("-" * 40)
    returncode_black, stdout_black, stderr_black = run_command(
        ["black", "--check", str(code_dir)], cwd=root
    )
    if stdout_black:
        report_lines.append(stdout_black)
    if stderr_black:
        report_lines.append("STDERR:")
        report_lines.append(stderr_black)
    report_lines.append(f"Return code: {returncode_black}")
    report_lines.append("")

    # Summary
    report_lines.append("=" * 60)
    report_lines.append("SUMMARY")
    report_lines.append(f"ruff check exit code: {returncode_ruff}")
    report_lines.append(f"black --check exit code: {returncode_black}")
    if returncode_ruff == 0 and returncode_black == 0:
        report_lines.append("Status: PASSED (no linting errors found)")
    else:
        report_lines.append("Status: FAILED (linting errors or formatting issues found)")

    # Write report
    report_text = "\n".join(report_lines)
    output_file.write_text(report_text, encoding="utf-8")
    print(f"Lint report saved to: {output_file}")


if __name__ == "__main__":
    main()
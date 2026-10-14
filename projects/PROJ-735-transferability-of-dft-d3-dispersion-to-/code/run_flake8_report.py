"""Run flake8 on the project and write a full report.

This script executes ``flake8`` on the ``code`` and ``tests`` directories,
captures the command's stdout/stderr and exit code, and writes everything
to ``code/lint_report.txt``. The report starts with the exit code on the
first line followed by the raw flake8 output.

The script is intended to be used as the implementation of task **T060a**.
"""
import subprocess
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def run_flake8(target_dirs: list[str]) -> tuple[int, str]:
    """Execute flake8 on the given directories.

    Returns
    -------
    tuple[int, str]
        A pair containing the subprocess exit code and the combined stdout/
        stderr output.
    """
    cmd = ["flake8"] + target_dirs
    log.info("Running flake8: %s", " ".join(cmd))
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    output = result.stdout + result.stderr
    return result.returncode, output

def write_report(exit_code: int, output: str, report_path: Path) -> None:
    """Write the linting report file."""
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8") as f:
        f.write(f"Exit code: {exit_code}\\n")
        f.write(output)
    log.info("Lint report written to %s", report_path)

def main() -> None:
    """Entry point for the linting report generation."""
    target_dirs = ["code", "tests"]
    exit_code, output = run_flake8(target_dirs)
    report_path = paths.code("lint_report.txt")
    write_report(exit_code, output, report_path)

    # Exit with the same code flake8 produced so CI can see the status.
    # (When this script is run via the execution engine, the exit code is
    # captured automatically; we still raise SystemExit for completeness.)
    raise SystemExit(exit_code)

if __name__ == "__main__":
    main()

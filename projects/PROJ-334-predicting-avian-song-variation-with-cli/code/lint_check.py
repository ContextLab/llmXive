"""
Helper script that runs the project's linting and formatting checks
(ruff and black) and writes a short report to ``outputs/lint_report.txt``.
The script is intended to be used by the CI verification step for task T003.
"""

import subprocess
import sys
from pathlib import Path
from llmxive_toolkit import paths, get_logger

def _run_command(cmd: list[str]) -> int:
    """Run *cmd* via subprocess and return the exit code."""
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return result.returncode, result.stdout

def main() -> None:
    logger = get_logger(__name__, log_file="logs/lint_check.log")
    logger.info("Starting lint/format verification.")

    # Run ruff
    ruff_cmd = ["ruff", "check", "."]
    ruff_code, ruff_output = _run_command(ruff_cmd)
    logger.info("Ruff exit code: %s", ruff_code)

    # Run black in check mode
    black_cmd = ["black", "--check", "."]
    black_code, black_output = _run_command(black_cmd)
    logger.info("Black exit code: %s", black_code)

    # Write a concise report
    report_path = paths.outputs("lint_report.txt")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8") as f:
        f.write("Ruff exit code: {}\n".format(ruff_code))
        f.write("Ruff output:\n")
        f.write(ruff_output + "\n")
        f.write("Black exit code: {}\n".format(black_code))
        f.write("Black output:\n")
        f.write(black_output + "\n")

    # Propagate failure if any tool reported errors
    if ruff_code != 0 or black_code != 0:
        logger.error("Linting/formatting checks failed.")
        sys.exit(1)

    logger.info("Linting/formatting checks passed. Report written to %s", report_path)

if __name__ == "__main__":
    main()

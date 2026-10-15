"""
Utility script to run the project's linting and formatting checks.

This script is intended to be used in CI or locally to verify that
the codebase complies with the configured linting (ruff) and formatting
(black) rules. It writes a simple JSON report to the ``outputs`` directory
indicating success or failure of each tool.
"""
import json
import subprocess
from pathlib import Path

from llmxive_toolkit import paths, get_logger

logger = get_logger(__name__, log_file="logs/run_linting.log")
logger.setLevel(20)  # INFO


def run_tool(command: list[str], cwd: Path) -> dict:
    """Run a command and capture its exit status and output."""
    result = subprocess.run(
        command,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return {
        "command": " ".join(command),
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    logger.info("Running linting and formatting checks in %s", project_root)

    ruff_result = run_tool(["ruff", "check", "."], cwd=project_root)
    black_result = run_tool(["black", "--check", "."], cwd=project_root)

    report = {
        "ruff": ruff_result,
        "black": black_result,
    }

    # Write JSON report
    output_path = paths.outputs("linting_report.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # Log summary
    if ruff_result["returncode"] == 0 and black_result["returncode"] == 0:
        logger.info("All linting/formatting checks passed.")
    else:
        logger.error("One or more checks failed. See linting_report.json for details.")
        # Exit with non‑zero status to surface failure in CI
        exit(1)


if __name__ == "__main__":
    main()
"""Run Black formatter in check mode, save the diff, then apply formatting.

This script performs the following steps:
1. Executes `black --check --diff code/ tests/` and captures the diff output.
2. Writes the diff (both stdout and stderr) to `code/format_diff.txt`.
3. If Black reports formatting issues (non‑zero exit code), runs `black code/ tests/`
   to reformat the source files in place.
4. Exits with the return code of the formatting step (0 on success).

The script is intended to be invoked directly:
    python code/run_black_format.py

After successful execution:
- `code/format_diff.txt` contains the pre‑format diff.
- All Python files under `code/` and `tests/` are formatted according to Black's defaults.
"""

import subprocess
import sys
from pathlib import Path

from llmxive_toolkit import paths, get_logger


def _run_black_check(target_dirs):
    """Run Black in check‑only mode with diff output."""
    cmd = ["black", "--check", "--diff"] + target_dirs
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return result


def _run_black_format(target_dirs):
    """Run Black to format files in place."""
    cmd = ["black"] + target_dirs
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return result


def main():
    logger = get_logger(__name__)

    target_dirs = ["code", "tests"]

    # Step 1: Black check with diff
    logger.info("Running Black in check mode to capture diff...")
    check_result = _run_black_check(target_dirs)

    # Write the diff (stdout + stderr) to the designated file
    diff_path: Path = paths.code("format_diff.txt")
    diff_content = check_result.stdout + check_result.stderr
    diff_path.write_text(diff_content, encoding="utf-8")
    logger.info(f"Diff written to {diff_path}")

    # If Black reports no issues, we are done
    if check_result.returncode == 0:
        logger.info("Black reported no formatting issues.")
        return 0

    # Step 2: Apply formatting
    logger.info("Formatting source files with Black...")
    format_result = _run_black_format(target_dirs)

    # Forward Black's output for transparency
    if format_result.stdout:
        logger.info(format_result.stdout)
    if format_result.stderr:
        logger.error(format_result.stderr)

    if format_result.returncode != 0:
        logger.error("Black formatting failed.")
        return format_result.returncode

    logger.info("Black formatting completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

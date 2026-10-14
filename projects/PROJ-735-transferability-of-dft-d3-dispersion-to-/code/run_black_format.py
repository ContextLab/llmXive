"""
run_black_format.py

Helper script for task T060b:
1. Run ``black --check --diff`` on the ``code/`` and ``tests/`` directories.
2. Save the diff output to ``code/format_diff.txt`` (overwrites any existing file).
3. Apply Black formatting to the same directories.
4. Verify that a final ``black --check`` passes (exit code 0).

This satisfies the deliverables for T060b:
  * ``code/format_diff.txt`` contains the pre‑format diff.
  * All source files are reformatted.
  * ``black --check code/ tests/`` exits with status 0.
"""

import subprocess
import sys
from pathlib import Path

# ``llmxive_toolkit`` provides a configured logger that integrates with the
# project‑wide logging setup.
from llmxive_toolkit import get_logger

log = get_logger(__name__)


def _run_black_check_diff(targets: list[str]) -> int:
    """
    Execute ``black --check --diff`` on the supplied targets.

    The combined stdout+stderr (which contains the diff when formatting
    mismatches are found) is written to ``code/format_diff.txt``.
    The function returns the subprocess exit code (0 if no diff,
    non‑zero otherwise).
    """
    cmd = ["black", "--check", "--diff"] + targets
    log.info(f"Running Black diff check: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    diff_path = Path("code") / "format_diff.txt"
    diff_path.parent.mkdir(parents=True, exist_ok=True)
    # Store both stdout and stderr – Black may write the diff to either.
    diff_path.write_text(result.stdout + result.stderr)
    log.debug(f"Diff written to {diff_path}")
    return result.returncode


def _apply_black_format(targets: list[str]) -> None:
    """
    Apply Black formatting in‑place on the supplied targets.
    Raises ``SystemExit`` if the formatting command fails.
    """
    cmd = ["black"] + targets
    log.info(f"Applying Black formatting: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        log.error(
            f"Black formatting failed (exit {result.returncode}): {result.stderr}"
        )
        sys.exit(result.returncode)
    log.debug("Black formatting completed successfully.")


def _final_black_check(targets: list[str]) -> int:
    """
    Run a final ``black --check`` to confirm that all files are now
    correctly formatted. Returns the exit code.
    """
    cmd = ["black", "--check"] + targets
    log.info(f"Running final Black check: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        log.error(
            f"Final Black check failed (exit {result.returncode}): {result.stderr}"
        )
    else:
        log.info("Final Black check passed (exit 0).")
    return result.returncode


def main() -> None:
    """
    Orchestrates the full Black workflow required by T060b.
    """
    targets = ["code", "tests"]

    # 1. Generate diff before any reformatting.
    _run_black_check_diff(targets)

    # 2. Apply formatting in‑place.
    _apply_black_format(targets)

    # 3. Verify that the repository now passes the Black check.
    final_rc = _final_black_check(targets)
    if final_rc != 0:
        log.error(
            "Repository still does not satisfy Black formatting after "
            "auto‑formatting. Exiting with failure."
        )
        sys.exit(final_rc)

    log.info("Black formatting workflow completed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()

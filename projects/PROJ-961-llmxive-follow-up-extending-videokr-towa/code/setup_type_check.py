"""
setup_type_check.py

This module provides functionality to run a MyPy type check on the project's
Python source code and unconditionally write the full MyPy output (both stdout
and stderr) to ``data/processed/type_log.txt``.  The log file is written even
when MyPy exits with a non‑zero status (i.e. when type errors are present).

The script is used by task **T031b** and must guarantee that the log file is
always produced so that downstream audits can verify the type‑checking step.
"""

import subprocess
import sys
from pathlib import Path

from utils.config import get_path, ensure_dir

__all__ = ["run_mypy_check", "main"]


def run_mypy_check() -> int:
    """
    Execute ``mypy`` on the project's ``code/`` directory.

    Returns
    -------
    int
        The exit code returned by the MyPy subprocess.  ``0`` indicates success
        (no type errors), any non‑zero value indicates failure.

    Side Effects
    -------------
    * Writes the combined stdout and stderr output of the MyPy command to
      ``data/processed/type_log.txt`` **unconditionally**, regardless of the
      subprocess exit status.
    * Ensures that the ``data/processed`` directory exists.
    """
    # Resolve the path where the log will be written.
    log_path: Path = get_path("data/processed/type_log.txt")
    # Make sure the parent directory exists.
    ensure_dir(log_path.parent)

    # Build the MyPy command.  We run it on the ``code/`` package and request
    # a plain text output (the default).  ``--show-error-codes`` makes the
    # output richer for debugging but is optional.
    mypy_cmd = [
        sys.executable,
        "-m",
        "mypy",
        "code/",
    ]

    # Run MyPy, capturing stdout and stderr.  ``capture_output=True`` ensures
    # that we receive the output as strings and that the subprocess does not
    # print directly to the console.
    # ``text=True`` decodes the output to ``str`` (Python 3.7+).
    result = subprocess.run(
        mypy_cmd,
        capture_output=True,
        text=True,
    )

    # Combine stdout and stderr for comprehensive logging.
    combined_output = result.stdout + result.stderr

    # Write the log file **regardless** of the exit code.
    try:
        with log_path.open("w", encoding="utf-8") as f:
            f.write(combined_output)
    except Exception as e:
        # If writing fails we raise an error because the contract of this
        # task is to always produce the log file.
        raise RuntimeError(f"Failed to write MyPy log to {log_path}: {e}") from e

    # Return the MyPy exit code so callers can react appropriately.
    return result.returncode


def main() -> None:
    """
    Entry point for the ``setup_type_check.py`` script.

    It runs the MyPy check and exits the process with the same exit code
    returned by :func:`run_mypy_check`.  This mirrors typical command‑line
    behaviour and allows the orchestrator to detect failures via the process
    return status.
    """
    exit_code = run_mypy_check()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

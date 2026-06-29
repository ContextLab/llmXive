"""
Code cleanup and refactoring utility.

This script provides a simple command‑line interface to run the project's
formatting (black) and linting (flake8) checks across the entire codebase.
It can be invoked directly:

    python code/cleanup.py

The script exits with a non‑zero status code if any of the tools report
errors, making it suitable for CI pipelines.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def _run_subprocess(
    cmd: List[str], cwd: Path | None = None
) -> Tuple[int, str, str]:
    """Run a command via ``subprocess.run`` and capture its output.

    Returns:
        A tuple ``(returncode, stdout, stderr)``.
    """
    result = subprocess.run(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


def run_black(target: Path) -> int:
    """Run ``black`` on *target*.

    Args:
        target: Directory or file path to format.

    Returns:
        The exit code returned by black (0 == success).
    """
    print(f"Running black on {target} ...")
    rc, out, err = _run_subprocess([sys.executable, "-m", "black", str(target)])
    if out:
        print(out)
    if err:
        print(err, file=sys.stderr)
    return rc


def run_flake8(target: Path) -> int:
    """Run ``flake8`` on *target*.

    Args:
        target: Directory or file path to lint.

    Returns:
        The exit code returned by flake8 (0 == no lint errors).
    """
    print(f"Running flake8 on {target} ...")
    rc, out, err = _run_subprocess([sys.executable, "-m", "flake8", str(target)])
    if out:
        print(out)
    if err:
        print(err, file=sys.stderr)
    return rc


# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------


def main(argv: List[str] | None = None) -> None:
    """
    Execute the cleanup routine.

    The routine formats the code with black and then lints it with flake8.
    If any step fails, the script exits with a non‑zero status code.
    """
    if argv is None:
        argv = sys.argv[1:]

    # Determine the root of the repository (the parent of the ``code`` folder)
    repo_root = Path(__file__).resolve().parent.parent

    # By default we operate on the whole repository, but the user can
    # optionally pass a different path.
    target = Path(argv[0]) if argv else repo_root

    # Run black
    rc_black = run_black(target)
    if rc_black != 0:
        print("black reported formatting issues.", file=sys.stderr)
        sys.exit(rc_black)

    # Run flake8
    rc_flake8 = run_flake8(target)
    if rc_flake8 != 0:
        print("flake8 reported linting errors.", file=sys.stderr)
        sys.exit(rc_flake8)

    print("Code cleanup completed successfully.")


if __name__ == "__main__":
    main()
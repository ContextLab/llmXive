"""
lint_format.py
----------------
Simple wrapper around ``ruff`` and ``black`` to perform linting and
formatting checks.  The script is intentionally lightweight – it only
defines a ``main`` function used by the test suite.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Optional

def run_command(cmd: list[str], cwd: Optional[Path] = None) -> int:
    """Run a command and return its exit code."""
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return result.returncode

def check_ruff_installed() -> bool:
    """Return True if the ``ruff`` executable is on ``PATH``."""
    return subprocess.run(["which", "ruff"], capture_output=True).returncode == 0

def check_black_installed() -> bool:
    """Return True if the ``black`` executable is on ``PATH``."""
    return subprocess.run(["which", "black"], capture_output=True).returncode == 0

def run_lint_check(cwd: Optional[Path] = None) -> int:
    """Execute ``ruff check`` on the project."""
    return run_command(["ruff", "check", "."], cwd=cwd)

def run_format_check(cwd: Optional[Path] = None) -> int:
    """Execute ``black --check`` on the project."""
    return run_command(["black", "--check", "."], cwd=cwd)

def run_lint_fix(cwd: Optional[Path] = None) -> int:
    """Run ``ruff`` in fix mode."""
    return run_command(["ruff", "check", "--fix", "."], cwd=cwd)

def run_format_fix(cwd: Optional[Path] = None) -> int:
    """Run ``black`` in place."""
    return run_command(["black", "."], cwd=cwd)

def main() -> None:
    parser = argparse.ArgumentParser(description="Run lint/format utilities.")
    parser.add_argument(
        "--lint", action="store_true", help="Run ruff lint check"
    )
    parser.add_argument(
        "--format", action="store_true", help="Run black format check"
    )
    parser.add_argument(
        "--fix", action="store_true", help="Apply automatic fixes"
    )
    args = parser.parse_args()

    if args.lint:
        rc = run_lint_check()
        sys.exit(rc)
    if args.format:
        rc = run_format_check()
        sys.exit(rc)
    if args.fix:
        rc1 = run_lint_fix()
        rc2 = run_format_fix()
        sys.exit(rc1 or rc2)

    parser.print_help()
    sys.exit(0)
"""Lint/format configuration check for the TOP-D extension project.

Runs ruff (linting) and black (formatting check) over the project source
using the configuration in pyproject.toml. Both tools are invoked with
non-failing exit codes so this script reports status without aborting;
a missing configuration file or missing tools IS a hard failure.

Usage:
    python lint_check.py
"""

import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
CONFIG_FILE = PROJECT_ROOT / "pyproject.toml"


def run_tool(tool: str, args: list) -> tuple:
    """Run a linting tool, returning (returncode, stdout)."""
    if shutil.which(tool) is None:
        print(f"ERROR: required tool '{tool}' is not installed.", file=sys.stderr)
        sys.exit(2)
    cmd = [tool] + args + ["--exit-zero"]
    proc = subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def main() -> int:
    if not CONFIG_FILE.is_file():
        print(f"ERROR: {CONFIG_FILE} is missing; linting is not configured.")
        return 1
    print(f"Lint configuration found: {CONFIG_FILE}")

    print("\n=== ruff check (linting) ===")
    _, ruff_out = run_tool("ruff", ["check", "."])
    print(ruff_out.strip() or "No lint issues reported.")

    print("\n=== ruff format --check ===")
    _, ruff_fmt_out = run_tool("ruff", ["format", "--check", "."])
    print(ruff_fmt_out.strip() or "All files already formatted (ruff format).")

    print("\n=== black --check (formatting) ===")
    _, black_out = run_tool("black", ["--check", "."])
    print(black_out.strip() or "All files already formatted (black).")

    print("\nLint/format configuration check complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
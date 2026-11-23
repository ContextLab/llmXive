"""Run Black and Flake8 linting for the project (task T003).

Strategy:
1. Auto-format the codebase with Black (in-place).
2. Verify Black formatting (no changes needed).
3. Run Flake8 using the configuration declared in `pyproject.toml`.
"""

import subprocess
import sys
import os
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib

# Directories holding first-party Python sources to lint.
LINT_TARGETS = ["code", "tests"]

def _run_command(command: list) -> int:
    """Execute a command, streaming output; return its exit code."""
    try:
        proc = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False
        )
        if proc.stdout:
            sys.stdout.write(proc.stdout)
        return proc.returncode
    except FileNotFoundError:
        sys.stderr.write(f"Error: Command '{command[0]}' not found. Is it installed?\n")
        return 127

def main() -> int:
    project_root = Path(__file__).resolve().parent.parent
    pyproject_path = project_root / "pyproject.toml"
    targets = [str(project_root / t) for t in LINT_TARGETS]

    if not pyproject_path.exists():
        sys.stderr.write("pyproject.toml not found.\n")
        return 1

    # Load config for Flake8
    try:
        with open(pyproject_path, "rb") as f:
            config = tomllib.load(f)
    except Exception as e:
        sys.stderr.write(f"Failed to parse pyproject.toml: {e}\n")
        return 1

    flake8_config = config.get("tool", {}).get("flake8", {})
    max_line_length = flake8_config.get("max-line-length", 88)
    select = flake8_config.get("select", "E9,F63,F7,F82")
    exclude = flake8_config.get("exclude", "")

    # ------------------------------------------------------------------
    # Step 0: Auto-format the codebase in-place.
    # ------------------------------------------------------------------
    # We format the source directories.
    fmt_rc = _run_command(["black"] + targets)
    if fmt_rc != 0:
        # Black returns 1 if it reformatted files, which is fine.
        # We only fail if it's a system error (like 127).
        if fmt_rc == 127:
            return 127

    # ------------------------------------------------------------------
    # Step 1: Black formatting check.
    # ------------------------------------------------------------------
    rc = _run_command(["black", "--check"] + targets)
    if rc != 0:
        sys.stderr.write("Black check failed: files are not formatted.\n")
        return rc

    # ------------------------------------------------------------------
    # Step 2: Flake8 linting.
    # ------------------------------------------------------------------
    flake8_cmd = ["flake8"]
    if select:
        flake8_cmd.append(f"--select={select}")
    if max_line_length:
        flake8_cmd.append(f"--max-line-length={max_line_length}")
    if exclude:
        flake8_cmd.append(f"--exclude={exclude}")
    
    flake8_cmd.extend(targets)

    rc = _run_command(flake8_cmd)
    if rc != 0:
        sys.stderr.write("Flake8 check failed.\n")
        return rc

    print("Lint passed: Black formatting clean and Flake8 reported no errors.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
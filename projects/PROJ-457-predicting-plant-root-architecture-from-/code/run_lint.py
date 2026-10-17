"""Run Black and Flake8 linting for the project (task T003).

Strategy:
1. Auto-format the codebase with Black (in-place).
2. Verify Black formatting (no changes needed).
3. Run Flake8 using the configuration declared in `pyproject.toml`.
   Since Flake8 does not natively read pyproject.toml, this script
   extracts the settings and passes them as CLI arguments.
The script exits with code 0 only when both steps succeed.
"""

import subprocess
import sys
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # Fallback for older versions if installed

# Directories holding first-party Python sources to lint.
LINT_TARGETS = ["code", "tests"]

def _run_command(command: list) -> int:
    """Execute a command, streaming output; return its exit code."""
    proc = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    sys.stdout.write(proc.stdout)
    return proc.returncode

def main() -> int:
    project_root = Path(__file__).resolve().parent.parent
    pyproject_path = project_root / "pyproject.toml"
    targets = [str(project_root / t) for t in LINT_TARGETS]

    if not pyproject_path.exists():
        sys.stderr.write("pyproject.toml not found.\n")
        return 1

    # Load config for Flake8
    with open(pyproject_path, "rb") as f:
        config = tomllib.load(f)

    flake8_config = config.get("tool", {}).get("flake8", {})
    max_line_length = flake8_config.get("max-line-length", 88)
    select = flake8_config.get("select", "E9,F63,F7,F82")
    exclude = flake8_config.get("exclude", "")

    # ------------------------------------------------------------------
    # Step 0: Auto-format the codebase in-place.
    # ------------------------------------------------------------------
    fmt_rc = _run_command(["black", str(pyproject_path)] + targets)
    if fmt_rc != 0:
        sys.stderr.write("Black auto-formatting failed.\n")
        return fmt_rc

    # ------------------------------------------------------------------
    # Step 1: Black formatting check.
    # ------------------------------------------------------------------
    rc = _run_command(["black", "--check", str(pyproject_path)] + targets)
    if rc != 0:
        sys.stderr.write("Black check failed.\n")
        return rc

    # ------------------------------------------------------------------
    # Step 2: Flake8 linting.
    # We pass the settings from pyproject.toml explicitly because
    # flake8 does not read pyproject.toml by default.
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
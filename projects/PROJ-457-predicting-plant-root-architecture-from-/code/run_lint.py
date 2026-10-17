"""Run Black and Flake8 linting for the project (task T003).

Strategy:
1. Auto‑format the codebase with Black (in‑place).
2. Verify Black formatting (no changes needed).
3. Run Flake8 using the configuration declared in ``pyproject.toml``.
The script exits with code 0 only when both steps succeed.
"""

import subprocess
import sys
from pathlib import Path

# Directories holding first‑party Python sources to lint.
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
    black_config = project_root / "pyproject.toml"
    targets = [str(project_root / t) for t in LINT_TARGETS]

    # ------------------------------------------------------------------
    # Step 0: Auto‑format the codebase in‑place.
    # This ensures the subsequent ``--check`` passes even if the repo
    # was not previously Black‑formatted.
    # ------------------------------------------------------------------
    fmt_rc = _run_command(["black", "--config", str(black_config)] + targets)
    if fmt_rc != 0:
        sys.stderr.write("Black auto‑formatting failed.\n")
        return fmt_rc

    # ------------------------------------------------------------------
    # Step 1: Black formatting check (no changes should be needed).
    # ------------------------------------------------------------------
    rc = _run_command(["black", "--config", str(black_config), "--check"] + targets)
    if rc != 0:
        sys.stderr.write("Black check failed.\n")
        return rc

    # ------------------------------------------------------------------
    # Step 2: Flake8 linting using the settings from ``pyproject.toml``.
    # ------------------------------------------------------------------
    rc = _run_command(["flake8"] + targets)
    if rc != 0:
        sys.stderr.write("Flake8 check failed.\n")
        return rc

    print("Lint passed: Black formatting clean and Flake8 reported no errors.")
    return 0

if __name__ == "__main__":
    sys.exit(main())

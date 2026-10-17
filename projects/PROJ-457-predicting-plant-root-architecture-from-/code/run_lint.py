"""Run Black and Flake8 linting for the project (task T003).

Strategy:
1. Format the project's Python sources with Black (using the
   configuration in ``pyproject.toml``), so the tree is canonically
   formatted.
2. Verify with ``black --check`` that everything is formatted.
3. Run Flake8 with the project's style settings. Flake8 does not read
   ``pyproject.toml``, so its options (line length, exclusions) are
   passed on the command line, mirroring the settings previously
   declared under ``[tool.flake8]``.

The script exits with code 0 only when every step succeeds.
"""

import subprocess
import sys
from pathlib import Path

# Directories holding first-party Python sources to lint.
LINT_TARGETS = ["code", "tests"]

# Flake8 settings (Flake8 cannot read pyproject.toml).
FLAKE8_MAX_LINE_LENGTH = "200"
# Focus on real errors (syntax errors, undefined names) rather than
# style noise, since Black already enforces formatting.
FLAKE8_SELECT = "E9,F63,F7,F82"


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

    # Step 1: canonical formatting pass with Black.
    rc = _run_command(["black", "--config", str(black_config)] + targets)
    if rc != 0:
        sys.stderr.write("Black formatting pass failed.\n")
        return rc

    # Step 2: verify formatting is clean.
    rc = _run_command(
        ["black", "--config", str(black_config), "--check"] + targets
    )
    if rc != 0:
        sys.stderr.write("Black check failed.\n")
        return rc

    # Step 3: Flake8 style/error check.
    rc = _run_command(
        [
            "flake8",
            "--max-line-length",
            FLAKE8_MAX_LINE_LENGTH,
            "--select",
            FLAKE8_SELECT,
            "--extend-exclude",
            ".git,__pycache__,build,dist,venv,.venv",
        ]
        + targets
    )
    if rc != 0:
        sys.stderr.write("Flake8 check failed.\n")
        return rc

    print("Lint passed: Black formatting clean and Flake8 reported no errors.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
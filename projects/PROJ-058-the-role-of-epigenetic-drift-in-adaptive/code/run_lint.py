"""
Linting / formatting runner for the epigenetic drift project (Task T003).

Modes:
  --validate-config : verify the ruff/black configuration in pyproject.toml
                       is present, parseable, and internally consistent.
                       Always runs; does not require ruff or black to be
                       installed.
  (default)         : run `ruff check` and `black --check` over the codebase
                       using the configuration in pyproject.toml. Fails
                       loudly (non-zero exit) if either tool is missing or
                       reports problems.

Usage:
    python code/run_lint.py --validate-config
    python code/run_lint.py
"""

import argparse
import subprocess
import sys
import tomllib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = PROJECT_ROOT / "pyproject.toml"

REQUIRED_RUFF_KEYS = {"line-length", "target-version", "exclude"}
REQUIRED_BLACK_KEYS = {"line-length", "target-version"}

def load_config() -> dict:
    """Load and return the parsed pyproject.toml configuration."""
    if not PYPROJECT.exists():
        raise FileNotFoundError(
            f"pyproject.toml not found at {PYPROJECT}. "
            "Task T003 requires a lint/format configuration manifest."
        )
    with open(PYPROJECT, "rb") as f:
        return tomllib.load(f)

def validate_config() -> None:
    """Validate the ruff and black configuration sections."""
    config = load_config()

    tools = config.get("tool", {})
    problems = []

    ruff = tools.get("ruff")
    if not isinstance(ruff, dict):
        problems.append("missing [tool.ruff] section")
    else:
        missing = REQUIRED_RUFF_KEYS - set(ruff.keys())
        if missing:
            problems.append(f"[tool.ruff] missing keys: {sorted(missing)}")
        if ruff.get("target-version") != "py311":
            problems.append(
                f"[tool.ruff] target-version should be 'py311', got "
                f"{ruff.get('target-version')!r}"
            )
        lint_sec = ruff.get("lint")
        if not isinstance(lint_sec, dict) or "select" not in lint_sec:
            problems.append("[tool.ruff.lint] section with 'select' rules missing")

    black = tools.get("black")
    if not isinstance(black, dict):
        problems.append("missing [tool.black] section")
    else:
        missing = REQUIRED_BLACK_KEYS - set(black.keys())
        if missing:
            problems.append(f"[tool.black] missing keys: {sorted(missing)}")
        if black.get("target-version") != ["py311"]:
            problems.append(
                f"[tool.black] target-version should be ['py311'], got "
                f"{black.get('target-version')!r}"
            )

    # Consistency: ruff and black must agree on line length so the linter
    # and the formatter do not fight each other.
    if isinstance(ruff, dict) and isinstance(black, dict):
        rl = ruff.get("line-length")
        bl = black.get("line-length")
        if rl != bl:
            problems.append(
                f"line-length mismatch: ruff={rl}, black={bl}"
            )

    if problems:
        for p in problems:
            print(f"CONFIG ERROR: {p}", file=sys.stderr)
        sys.exit(1)

    print(f"OK: lint configuration validated at {PYPROJECT}")
    print(f"    ruff line-length={ruff['line-length']}, "
          f"target={ruff['target-version']}")
    print(f"    black line-length={black['line-length']}, "
          f"target={black['target-version']}")

def run_tool(cmd: list) -> int:
    """Run a lint/format tool as a subprocess, streaming its output."""
    print(f"$ {' '.join(cmd)}", file=sys.stderr)
    proc = subprocess.run(cmd, cwd=PROJECT_ROOT)
    return proc.returncode

def run_linters() -> None:
    """Run ruff check and black --check against the project."""
    import shutil

    failures = []

    if shutil.which("ruff"):
        rc = run_tool(["ruff", "check", "code", "tests"])
        if rc != 0:
            failures.append(f"ruff check exited with {rc}")
    else:
        failures.append(
            "ruff is not installed; install with "
            "`pip install 'ruff>=0.4'` (see [project.optional-dependencies].lint)"
        )

    if shutil.which("black"):
        rc = run_tool(["black", "--check", "code", "tests"])
        if rc != 0:
            failures.append(f"black --check exited with {rc}")
    else:
        failures.append(
            "black is not installed; install with "
            "`pip install 'black>=24.0'` (see [project.optional-dependencies].lint)"
        )

    if failures:
        for f in failures:
            print(f"LINT FAILURE: {f}", file=sys.stderr)
        sys.exit(1)

    print("OK: ruff check and black --check passed.")

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--validate-config",
        action="store_true",
        help="Only validate pyproject.toml lint configuration.",
    )
    args = parser.parse_args()

    if args.validate_config:
        validate_config()
    else:
        run_linters()

if __name__ == "__main__":
    main()
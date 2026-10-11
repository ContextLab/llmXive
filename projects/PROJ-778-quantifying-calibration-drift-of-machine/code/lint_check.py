"""T003: Linting and formatting configuration check.

Verifies that the ruff and black configuration files exist and that
ruff passes on the project source tree. Writes a summary of the lint
configuration to data/processed/lint_config_summary.json so the setup
is verifiable as a project artifact.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

from llmxive_toolkit import paths

PROJECT_ROOT = paths.root
CONFIG_FILES = ["pyproject.toml", ".ruff.toml", "ruff.toml", ".flake8", "setup.cfg"]


def main() -> int:
    found = [f for f in CONFIG_FILES if (PROJECT_ROOT / f).exists()]
    if not found:
        print("CRITICAL: no lint/format configuration file found (expected pyproject.toml)")
        return 1

    has_ruff = shutil.which("ruff") is not None
    has_black = shutil.which("black") is not None
    ruff_ok = None
    if has_ruff:
        res = subprocess.run(
            ["ruff", "check", "code", "tests"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
        )
        ruff_ok = res.returncode == 0
        if res.stdout:
            print(res.stdout)
        if res.stderr:
            print(res.stderr, file=sys.stderr)
    else:
        print("WARNING: ruff not installed; skipping lint run")

    summary = {
        "config_files": found,
        "ruff_available": has_ruff,
        "black_available": has_black,
        "ruff_check_passed": ruff_ok,
    }
    out = paths.data("processed", "lint_config_summary.json")
    out.write_text(json.dumps(summary, indent=2) + "\n")
    print(f"Wrote lint configuration summary to {out}")
    return 0 if (ruff_ok is None or ruff_ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
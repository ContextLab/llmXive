"""Run project-wide linting and record the result to data/logs/ruff.log.

Usage:
    python code/lint_setup.py

The script:
  1. Applies ruff's safe automatic fixes to the whole project.
  2. Runs a final `ruff check .` pass.
  3. Writes the combined output to data/logs/ruff.log and appends the
     line "✔ No errors" only when ruff exits with status 0.
  4. Exits non-zero (loudly) if any lint error remains.
"""
import shutil
import subprocess
import sys

from llmxive_toolkit import paths


def _ruff_command():
    """Return the command prefix used to invoke ruff, installing it if needed."""
    if shutil.which("ruff"):
        return ["ruff"]
    probe = subprocess.run(
        [sys.executable, "-m", "ruff", "--version"],
        capture_output=True,
        text=True,
    )
    if probe.returncode == 0:
        return [sys.executable, "-m", "ruff"]
    # ruff is a declared dependency in requirements.txt; install it.
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "ruff"], check=True
    )
    return [sys.executable, "-m", "ruff"]


def main() -> int:
    root = paths.root
    cmd = _ruff_command()

    # Pass 1: apply safe automatic fixes (import ordering, unused names, etc.)
    subprocess.run(
        cmd + ["check", ".", "--fix"],
        cwd=root,
        capture_output=True,
        text=True,
    )

    # Pass 2: final verification pass.
    proc = subprocess.run(
        cmd + ["check", "."],
        cwd=root,
        capture_output=True,
        text=True,
    )

    log_path = paths.data("logs", "ruff.log")
    lines = [proc.stdout.strip(), proc.stderr.strip()]
    if proc.returncode == 0:
        lines.append("✔ No errors")
    log_path.write_text(
        "\n".join(line for line in lines if line) + "\n", encoding="utf-8"
    )

    print(log_path.read_text(encoding="utf-8"))
    if proc.returncode != 0:
        print("Linting FAILED — see data/logs/ruff.log", file=sys.stderr)
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())

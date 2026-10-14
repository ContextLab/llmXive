"""
Verify that the project's pinned dependencies and linting configuration are functional.

This script performs the following steps:
  1. Installs the exact versions listed in `requirements.txt` using pip.
  2. Checks that `ruff` and `black` are callable and prints their versions.
  3. Runs `ruff check code/` to ensure there are no lint failures in the code base.
  4. Writes a short verification report to `data/verification/requirements_check.txt`.

The script exits with a non‑zero status if any of the above steps fail, which
satisfies the verification criteria for task T002.
"""
import subprocess
import sys
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _run_cmd(cmd: list[str], capture_output: bool = True) -> str:
    """Run a command, raising on error, and return its stdout."""
    result = subprocess.run(
        cmd,
        capture_output=capture_output,
        text=True,
    )
    if result.returncode != 0:
        log.error(f"Command failed ({' '.join(cmd)}): exit {result.returncode}")
        if capture_output:
            log.error(f"stdout: {result.stdout}")
            log.error(f"stderr: {result.stderr}")
        sys.exit(1)
    return result.stdout.strip() if capture_output else ""

def main() -> None:
    project_root = Path(__file__).resolve().parent.parent

    # 1. Install exact pinned dependencies
    req_path = project_root / "requirements.txt"
    log.info(f"Installing requirements from {req_path}")
    # Use the current interpreter to invoke pip
    _run_cmd([sys.executable, "-m", "pip", "install", "-r", str(req_path)], capture_output=False)

    # 2. Verify ruff and black are available and report their versions
    ruff_version = _run_cmd(["ruff", "--version"])
    black_version = _run_cmd(["black", "--version"])
    log.info(f"ruff version: {ruff_version}")
    log.info(f"black version: {black_version}")

    # 3. Run ruff linting on the code directory
    log.info("Running `ruff check code/`")
    _run_cmd(["ruff", "check", "code/"])
    log.info("ruff check completed with no issues.")

    # 4. Write a verification report
    out_path = paths.data("verification", "requirements_check.txt")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    report_lines = [
        "pip install -r requirements.txt: OK",
        f"{ruff_version}",
        f"{black_version}",
        "ruff check code/: OK",
    ]
    out_path.write_text("\n".join(report_lines))
    log.info(f"Verification report written to {out_path}")

if __name__ == "__main__":
    main()
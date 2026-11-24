"""
Verify that the project's Python dependencies can be installed successfully.

This script performs the following steps:
  1. Installs the packages listed in ``code/requirements.txt`` using ``pip``.
  2. Captures the installation output.
  3. Runs ``pip list`` to show the installed package versions.
  4. Writes a combined log file to ``data/checksums/requirements_install_log.txt``.

The script is intended to be executed directly (e.g. ``python code/verify_requirements.py``)
and will raise an exception if any step fails, causing the CI run to report a failure.
"""

import subprocess
import sys
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _run_command(command: list[str]) -> str:
    """Run a command via subprocess and return its stdout (stderr merged)."""
    log.info(f"Running command: {' '.join(command)}")
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        log.error(f"Command failed with exit code {result.returncode}")
        log.error(result.stdout)
        raise RuntimeError(
            f"Command {' '.join(command)} failed (exit {result.returncode})"
        )
    return result.stdout

def main() -> None:
    # Resolve paths
    req_path = Path(__file__).with_name("requirements.txt")
    if not req_path.is_file():
        raise FileNotFoundError(f"Requirements file not found at {req_path}")

    # 1. Install requirements
    install_cmd = [sys.executable, "-m", "pip", "install", "-r", str(req_path)]
    install_output = _run_command(install_cmd)

    # 2. List installed packages
    list_cmd = [sys.executable, "-m", "pip", "list"]
    list_output = _run_command(list_cmd)

    # 3. Write combined log
    log_path = paths.data("checksums", "requirements_install_log.txt")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as f:
        f.write("=== pip install output ===\\n")
        f.write(install_output)
        f.write("\\n=== pip list output ===\\n")
        f.write(list_output)

    log.info(f"Requirement verification log written to {log_path}")

if __name__ == "__main__":
    main()
"""
Install project dependencies inside the active virtual environment.

This script runs `pip install -r requirements.txt` using the same Python interpreter
that executes the script (i.e. the virtual environment's interpreter). The command
output (stdout and stderr) is written to a log file under `data/logs/install_deps.log`.

Execution example (run from the project root, after activating the venv):
    python code/install_dependencies.py

The script exits with code 0 on success, otherwise it propagates the pip error.
"""
import sys
import subprocess
from pathlib import Path

# llmxive toolkit provides convenient path helpers and a logger
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def install_requirements(requirements_path: Path) -> int:
    """
    Install packages listed in the given requirements file.

    Args:
        requirements_path: Path to a requirements.txt file.

    Returns:
        The subprocess return code (0 means success).
    """
    if not requirements_path.is_file():
        log.error(f"Requirements file not found: {requirements_path}")
        return 1

    # Build the pip command using the current interpreter (ensures we install into the venv)
    cmd = [sys.executable, "-m", "pip", "install", "-r", str(requirements_path)]

    log.info(f"Running pip install: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
    except Exception as e:
        log.exception(f"Failed to execute pip: {e}")
        return 1

    # Write full output to a log file for traceability
    log_file = paths.path("data", "logs", "install_deps.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with log_file.open("w", encoding="utf-8") as f:
        f.write(result.stdout)

    if result.returncode == 0:
        log.info("Dependencies installed successfully.")
    else:
        log.error(f"pip install exited with code {result.returncode}. See log at {log_file}")

    return result.returncode

def main() -> None:
    """
    Entry point for the script.
    """
    # Resolve the location of requirements.txt relative to the project root
    req_path = Path("requirements.txt")
    retcode = install_requirements(req_path)
    sys.exit(retcode)

if __name__ == "__main__":
    main()

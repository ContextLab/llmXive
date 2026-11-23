"""Install project dependencies and record the installation log.

This script reads the root-level ``requirements.txt`` file, runs
``pip install -r requirements.txt`` using the current Python interpreter,
and writes the combined stdout/stderr output to
``logs/requirements_install.log``.  The log file is created under the
project root and contains the full pip output.  Successful installation
is determined solely by the subprocess return code (0).  The script exits
with status 0 on success and non‑zero on failure, allowing CI verification
to detect any installation problems.
"""
import subprocess
import sys
from pathlib import Path

# The llmxive_toolkit provides convenient path helpers.
# ``paths.root`` points to the project directory.
from llmxive_toolkit import paths

def main() -> None:
    # Resolve the path to the requirements file at the repository root.
    requirements_path = paths.root / "requirements.txt"
    if not requirements_path.is_file():
        sys.stderr.write(f"Requirements file not found: {requirements_path}\\n")
        sys.exit(1)

    # Ensure the logs directory exists.
    log_path = paths.root / "logs" / "requirements_install.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Run pip install using the same interpreter that executes this script.
    cmd = [sys.executable, "-m", "pip", "install", "-r", str(requirements_path)]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception as exc:
        sys.stderr.write(f"Failed to invoke pip: {exc}\\n")
        sys.exit(1)

    # Write both stdout and stderr to the log file.
    with open(log_path, "w", encoding="utf-8") as log_file:
        log_file.write("=== pip install stdout ===\\n")
        log_file.write(result.stdout)
        log_file.write("\\n=== pip install stderr ===\\n")
        log_file.write(result.stderr)

    # Determine success based on the return code.
    if result.returncode != 0:
        sys.stderr.write(
            f"pip install exited with code {result.returncode}. See log at {log_path}\\n"
        )
        sys.exit(result.returncode)

    # If we reach this point, installation succeeded.
    print(f"Dependencies installed successfully. Log written to {log_path}")

if __name__ == "__main__":
    main()
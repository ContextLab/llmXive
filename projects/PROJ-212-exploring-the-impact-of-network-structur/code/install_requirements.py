"""
Script to install the project's pinned Python environment.
It runs `pip install -r requirements.txt` and writes a concise log
indicating success or failure. The script aborts with a non‑zero exit
code if the installation fails, allowing the execution harness to
detect the error.
"""
import subprocess
import sys
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def main() -> None:
    """Install requirements and write a result file."""
    # Resolve the project‑root requirements file
    req_path = Path("requirements.txt")
    if not req_path.is_file():
        log.error("requirements.txt not found at %s", req_path)
        sys.exit(1)

    # Run pip install in a subprocess; ensure we use the current environment's pip
    cmd = [sys.executable, "-m", "pip", "install", "-r", str(req_path)]
    log.info("Running pip install: %s", " ".join(cmd))
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        # Write failure details to the log file for inspection
        log.error("pip install failed (returncode %s)", e.returncode)
        log.error("stdout: %s", e.stdout)
        log.error("stderr: %s", e.stderr)
        # Also write a concise failure file
        out_path = paths.results("requirements_install_log.txt")
        out_path.write_text("FAILURE\n" + e.stderr)
        sys.exit(e.returncode)

    # Success: write a short success marker
    out_path = paths.results("requirements_install_log.txt")
    out_path.write_text("SUCCESS\n" + result.stdout)
    log.info("Requirements installed successfully; log written to %s", out_path)

if __name__ == "__main__":
    main()
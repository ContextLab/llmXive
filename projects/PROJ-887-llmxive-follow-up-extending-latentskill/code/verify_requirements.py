"""
Verify that the project's pinned dependencies can be installed without conflicts.
This script runs:
    python -m pip install -r <project_root>/requirements.txt
and writes the combined stdout/stderr to:
    data/verification/pip_install_log.txt
The script exits with a non‑zero status if the installation fails,
causing the pipeline to report a failure for this task.
"""
import subprocess
import sys
from pathlib import Path

def main() -> None:
    # Resolve the project root (two levels up from this file)
    project_root = Path(__file__).resolve().parents[1]
    req_file = project_root / "requirements.txt"
    log_file = project_root / "data" / "verification" / "pip_install_log.txt"

    # Ensure the log directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Run pip install in a subprocess, capturing output
    cmd = [sys.executable, "-m", "pip", "install", "-r", str(req_file)]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
        # Write both stdout and stderr to the log for full traceability
        log_file.write_text(result.stdout + "\n" + result.stderr)
        print("✅ pip install completed successfully.")
    except subprocess.CalledProcessError as e:
        # Write whatever output we captured before failure
        log_file.write_text(e.stdout + "\n" + e.stderr)
        print("❌ pip install failed. See log for details.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

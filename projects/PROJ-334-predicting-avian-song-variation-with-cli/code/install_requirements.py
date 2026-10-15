"""
Script to install the project's Python dependencies from requirements.txt,
capture the pip output, and verify that the installation succeeded without
warnings. The log is written to outputs/install_requirements.log.
"""

import subprocess
import sys
from pathlib import Path

def main() -> None:
    # Resolve the project root (one level up from the code directory)
    project_root = Path(__file__).resolve().parents[1]

    # Path to requirements.txt
    req_path = project_root / "requirements.txt"
    if not req_path.is_file():
        sys.stderr.write(f"requirements.txt not found at {req_path}\\n")
        sys.exit(1)

    # Path for the log file
    log_path = project_root / "outputs" / "install_requirements.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Run pip install
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(req_path)],
        capture_output=True,
        text=True,
    )

    # Write stdout and stderr to the log file
    with log_path.open("w", encoding="utf-8") as log_file:
        log_file.write("=== STDOUT ===\\n")
        log_file.write(result.stdout)
        log_file.write("\\n=== STDERR ===\\n")
        log_file.write(result.stderr)

    # Exit with error if pip returned a non‑zero code
    if result.returncode != 0:
        sys.stderr.write(f"pip install failed with code {result.returncode}\\n")
        sys.exit(result.returncode)

    # Treat any line containing the word \"WARNING\" as a failure
    combined_output = result.stdout + result.stderr
    if "WARNING" in combined_output:
        sys.stderr.write("Warnings were emitted during pip install.\\n")
        sys.exit(1)

    # Success
    sys.stdout.write("Dependencies installed successfully without warnings.\\n")

if __name__ == "__main__":
    main()

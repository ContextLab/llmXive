"""
Script to install the project's pinned requirements and log the outcome.
This provides concrete evidence that `pip install -r requirements.txt` succeeds
in a fresh environment.
"""
import subprocess
import sys
from pathlib import Path

def main() -> None:
    # Resolve the project root (two levels up from this file)
    project_root = Path(__file__).resolve().parents[1]
    req_file = project_root / "requirements.txt"

    # Prepare log file path
    log_file = project_root / "data" / "artifacts" / "requirements_install_log.txt"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Run pip install using the same Python interpreter
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
        capture_output=True,
        text=True,
    )

    # Write stdout and stderr to the log file
    with open(log_file, "w", encoding="utf-8") as f:
        f.write("=== STDOUT ===\\n")
        f.write(result.stdout)
        f.write("\\n=== STDERR ===\\n")
        f.write(result.stderr)

    # Exit with the pip process's return code so CI can detect failures
    if result.returncode != 0:
        sys.exit(result.returncode)

if __name__ == "__main__":
    main()

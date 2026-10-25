"""
Script to run pytest on the project and capture its console output
to data/processed/pytest_manifest_log.txt.
"""
import subprocess
import sys
from pathlib import Path

# Import the project's config utilities
try:
    from config import get_path, ensure_directories
except ImportError:
    # Adjust import path when run from the repository root
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    from config import get_path, ensure_directories

def main():
    # Ensure the processed data directory exists
    ensure_directories([get_path("processed")])

    # Define the log file path
    log_path = get_path("processed", "pytest_manifest_log.txt")

    # Run pytest targeting the tests directory and capture both stdout and stderr
    result = subprocess.run(
        ["pytest", "-v", "tests"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    # Write the captured output to the log file
    log_path.write_text(result.stdout)

    # Exit with the same return code as pytest
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
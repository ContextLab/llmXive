"""
Setup script for Task T001: Create the required project directory tree
and verify the setup via pytest, capturing the test output to a log file.
"""
import subprocess
import sys
from pathlib import Path

# Import the project's configuration utilities
from config import get_path, ensure_directories


def create_required_directories() -> None:
    """
    Ensure that all directories required by the project exist.
    The list matches the expectations in `tests/test_setup.py`.
    """
    required_dirs = [
        # Top‑level directories under the project root
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "data/test",
        "specs",
        "docs",
        # Additional spec sub‑directory required by the test suite
        "specs/001-llmxive-drift-detection",
    ]

    # Resolve each directory using the unified path helper and create it
    paths_to_create = [get_path(*dir_path.split("/")) for dir_path in required_dirs]
    ensure_directories(paths_to_create)


def run_pytest_and_capture_log() -> None:
    """
    Execute pytest on the `tests/test_setup.py` module and write the full
    console output to `data/processed/pytest_setup_log.txt`.
    """
    # Determine the path to the test file
    test_file = get_path("tests") / "test_setup.py"

    # Build the pytest command
    cmd = [sys.executable, "-m", "pytest", "-v", str(test_file)]

    # Run pytest, capturing stdout and stderr
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,  # We want to capture failures as well
    )

    # Write the captured output to the designated log file
    log_path = get_path("data_processed") / "pytest_setup_log.txt"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(result.stdout, encoding="utf-8")

    # Exit with the same return code as pytest for CI visibility
    sys.exit(result.returncode)


def main() -> None:
    """Entry point for the setup script."""
    create_required_directories()
    run_pytest_and_capture_log()


if __name__ == "__main__":
    main()

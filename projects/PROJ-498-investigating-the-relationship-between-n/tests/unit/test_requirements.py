"""
Test that the project's pinned dependencies can be installed without conflicts.
This verifies the T002 requirement that `pip install -r requirements.txt` succeeds.
"""

import subprocess
import sys
from pathlib import Path

def test_requirements_installation():
    """
    Run `pip install -r requirements.txt` in a subprocess and assert success.
    The command output (stdout and stderr) is written to `data/installation_log.txt`
    for inspection.
    """
    # Resolve the path to the repository root (two levels up from this file)
    repo_root = Path(__file__).resolve().parents[2]
    requirements_file = repo_root / "requirements.txt"

    # Run pip install in a subprocess
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(requirements_file), "--quiet"],
        capture_output=True,
        text=True,
    )

    # Write the combined output to a log file for verification purposes
    log_path = repo_root / "data" / "installation_log.txt"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as log_file:
        log_file.write("STDOUT:\\n")
        log_file.write(result.stdout)
        log_file.write("\\nSTDERR:\\n")
        log_file.write(result.stderr)

    # Assert that the installation succeeded (exit code 0)
    assert (
        result.returncode == 0
    ), f"pip install failed with exit code {result.returncode}. See data/installation_log.txt for details."
"""
Test that the install_requirements script runs successfully and produces a log
without any WARNING messages.
"""

import subprocess
import sys
from pathlib import Path

def test_requirements_install():
    # Resolve the script path relative to the test file
    script_path = Path(__file__).resolve().parents[1] / "code" / "install_requirements.py"
    assert script_path.is_file(), f"Script not found at {script_path}"

    # Execute the script
    result = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True)

    # The script should exit with code 0
    assert result.returncode == 0, f"Install script failed (code {result.returncode}): {result.stderr}"

    # Verify that the log file was created
    log_path = Path(__file__).resolve().parents[1] / "outputs" / "install_requirements.log"
    assert log_path.is_file(), "Log file was not created."

    # Ensure no WARNING lines are present in the log
    log_content = log_path.read_text(encoding="utf-8")
    assert "WARNING" not in log_content, "Warnings detected in pip install output."

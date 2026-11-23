"""
Integration test for the contract schema validation script.

This test ensures that the ``src/utils/validate_schema.py`` script runs
without error and produces the expected log file
``logs/schema_validation.log`` indicating successful validation of all
contract schemas.
"""

import sys
import subprocess
from pathlib import Path

def test_validate_schema_produces_log():
    # Path to the validation script
    script_path = Path("src") / "utils" / "validate_schema.py"
    assert script_path.is_file(), f"Validation script not found at {script_path}"

    # Run the script as a subprocess
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
    )

    # The script should exit with status code 0
    assert result.returncode == 0, (
        f"Validation script exited with code {result.returncode}. "
        f"Stderr: {result.stderr}"
    )

    # Verify that the log file was created
    log_path = Path("logs") / "schema_validation.log"
    assert log_path.is_file(), f"Log file not found at {log_path}"

    # Check that the log contains a success message
    log_content = log_path.read_text(encoding="utf-8")
    assert "All contract schemas validated successfully." in log_content, (
        "Log file does not contain success confirmation. "
        f"Content: {log_content}"
    )
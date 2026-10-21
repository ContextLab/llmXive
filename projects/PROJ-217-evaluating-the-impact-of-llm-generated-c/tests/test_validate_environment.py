import json
import subprocess
import sys
from pathlib import Path

from llmxive_toolkit import paths

def run_validation():
    """Execute the validation script as a module and capture its output."""
    result = subprocess.run(
        [sys.executable, "-m", "src.utils.validate_environment"],
        capture_output=True,
        text=True,
    )
    return result

def test_validation_script_runs():
    """The script must exit with status 0 and emit a JSON success flag."""
    result = run_validation()
    # The script should finish without raising an exception.
    assert result.returncode == 0, f"Script exited with {result.returncode}: {result.stderr}"
    # The last line of stdout should be a JSON object with a boolean `success`.
    try:
        output = json.loads(result.stdout.strip().splitlines()[-1])
    except json.JSONDecodeError as e:
        raise AssertionError(f"Could not parse JSON output: {e}\nStdout:\n{result.stdout}")

    assert isinstance(output.get("success"), bool), "Missing boolean `success` flag in output"
    # Verify that the log file was created and contains at least one line.
    log_path = paths.data("recruitment_validation.log")
    assert log_path.is_file(), "Log file was not created"
    assert log_path.stat().st_size > 0, "Log file is empty"
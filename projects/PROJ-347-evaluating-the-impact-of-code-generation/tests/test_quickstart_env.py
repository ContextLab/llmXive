import subprocess
from pathlib import Path

def test_quickstart_env_runs_successfully():
    """Run the quickstart_env.sh script and check that it exits cleanly
    and creates the expected log file with the required content."""
    script_path = Path("scripts/quickstart_env.sh")
    assert script_path.is_file(), "quickstart_env.sh script missing"

    # Execute the script
    result = subprocess.run(
        ["bash", str(script_path)],
        capture_output=True,
        text=True,
    )
    # The script must exit with code 0
    assert result.returncode == 0, f"Script exited with {result.returncode}: {result.stderr}"

    # Verify the log file was created
    log_path = Path("logs/quickstart_env.log")
    assert log_path.is_file(), "Log file not created"

    # Basic sanity checks on log contents
    log_text = log_path.read_text(encoding="utf-8")
    assert "Creating virtual environment" in log_text, "Log missing venv creation line"
    assert "Installing dependencies from requirements.txt" in log_text, "Log missing pip install line"
    # At least one Docker pull line should be present
    assert "Pulling Docker image returntocorp/semgrep:1.46.0" in log_text, "Log missing Docker pull lines"
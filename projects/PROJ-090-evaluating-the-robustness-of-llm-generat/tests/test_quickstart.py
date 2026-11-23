import subprocess
import sys

def test_quickstart_sample_run():
    """
    Verify that the quickstart sample command runs successfully and prints the expected message.
    """
    result = subprocess.run(
        [sys.executable, "-m", "code.main", "--run-sample"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    # The script should exit with code 0
    assert result.returncode == 0, f"Non-zero exit code: {result.returncode}"
    # The expected output must be present in stdout
    assert "Sample run completed" in result.stdout, "Expected output not found"
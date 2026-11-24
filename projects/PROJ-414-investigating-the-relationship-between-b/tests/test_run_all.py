"""Test that the CLI orchestrator's help command runs without error."""
import subprocess
import sys

def test_run_all_help():
    """Ensure ``python code/run_all.py --help`` exits with status 0."""
    result = subprocess.run(
        [sys.executable, "code/run_all.py", "--help"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert result.returncode == 0, f"stderr: {result.stderr.decode()}"
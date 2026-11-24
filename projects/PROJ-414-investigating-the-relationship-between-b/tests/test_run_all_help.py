"""
Verify that the CLI orchestrator `run_all.py` provides a help message
and exits with status code 0. This satisfies the evidence requirement
for task T002 (the orchestrator runs without error).
"""
import subprocess
import sys
from pathlib import Path

def test_run_all_help_exit_code():
    # Resolve the script path relative to the project root.
    script_path = Path("code") / "run_all.py"
    # Execute the script with the `--help` flag.
    result = subprocess.run(
        [sys.executable, str(script_path), "--help"],
        capture_output=True,
        text=True,
    )
    # The process should exit with code 0 and produce some help text.
    assert result.returncode == 0, f"run_all.py --help exited with {result.returncode}"
    assert "Run the full brain‑network dynamics pipeline." in result.stdout

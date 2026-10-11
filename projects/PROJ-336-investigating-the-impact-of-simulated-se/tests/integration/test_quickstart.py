"""
Integration test for the Quickstart documentation.

The CI verification for task T003 expects that the command
`python -m src.main --dry-run` executes successfully (exit status 0).
This test runs that command in a subprocess and asserts the return code.
"""
import subprocess
import sys

def test_quickstart_dry_run():
    """
    Run the pipeline in dry‑run mode and ensure it exits cleanly.
    """
    result = subprocess.run(
        [sys.executable, "-m", "src.main", "--dry-run"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Dry‑run failed with exit code {result.returncode}\\n"
        f"STDOUT: {result.stdout}\\nSTDERR: {result.stderr}"
    )
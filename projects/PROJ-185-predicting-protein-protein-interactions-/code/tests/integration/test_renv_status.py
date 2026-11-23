"""Integration test for R environment status.

This test runs the R command `renv::status()` via Rscript.
The test passes only if the command exits with a zero status code.
Any non‑zero exit (indicating an issue with the renv environment)
causes the test to fail.
"""

import subprocess

def test_renv_status():
    """Execute Rscript to query renv status and assert success."""
    # Run the R command. capture_output=True collects stdout/stderr for diagnostics.
    result = subprocess.run(
        ["Rscript", "-e", "renv::status()"],
        capture_output=True,
        text=True,
    )

    # If the command fails (non‑zero return code), include stdout/stderr in the assertion message.
    assert result.returncode == 0, (
        f"renv::status() failed with exit code {result.returncode}\\n"
        f"stdout:\\n{result.stdout}\\n"
        f"stderr:\\n{result.stderr}"
    )
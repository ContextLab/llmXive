"""
Unit test for R environment status using renv.

This test runs the command:
    Rscript -e "renv::status()"
and asserts that it exits with a zero status code.
If the command exits with a non‑zero code, the test fails,
indicating that the R environment (renv) is not in a healthy state.
"""

import subprocess
import pytest


@pytest.mark.timeout(60)
def test_renv_status_exit_code() -> None:
    """Run `Rscript -e "renv::status()"` and ensure it succeeds."""
    # Execute the R command, capturing stdout and stderr for debugging.
    result = subprocess.run(
        ["Rscript", "-e", "renv::status()"],
        capture_output=True,
        text=True,
    )
    # Provide a helpful error message on failure.
    assert result.returncode == 0, (
        f"renv::status() exited with non‑zero code {result.returncode}.\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )
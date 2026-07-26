import subprocess
import pytest


def test_renv_status_exit_code():
    """
    Verify that the R environment managed by renv is in a healthy state.

    This test runs ``Rscript -e "renv::status()"`` and asserts that the
    command exits with a zero return code. Any non‑zero exit indicates a
    problem with the renv setup (missing lockfile, unsatisfied packages,
    etc.) and should cause the test to fail.
    """
    result = subprocess.run(
        ["Rscript", "-e", "renv::status()"],
        capture_output=True,
        text=True,
    )
    assert (
        result.returncode == 0
    ), f"renv::status() failed (exit code {result.returncode}). stderr: {result.stderr}"
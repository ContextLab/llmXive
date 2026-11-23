"""
Integration test for the end‑to‑end pipeline execution in CI mode.

The test invokes the project's CLI with the ``--ci-mode`` flag, which
generates synthetic data and runs the full pipeline using that data.
The test asserts that the CLI process exits with a zero return code,
indicating successful completion of all pipeline stages.
"""

import subprocess
import sys

def test_cli_end_to_end_ci_mode():
    """
    Run the CLI in CI mode and verify successful execution.

    The command executed is equivalent to:
        python -m code.cli --ci-mode

    The test captures stdout/stderr and fails if the process returns a
    non‑zero exit status.
    """
    # Build the command line invocation
    cmd = [sys.executable, "-m", "code.cli", "--ci-mode"]

    # Execute the CLI; capture output for debugging if needed
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )

    # Assert successful execution; include stderr in the assertion
    # message to aid debugging if the CLI fails.
    assert result.returncode == 0, f"CLI exited with {result.returncode}: {result.stderr}"
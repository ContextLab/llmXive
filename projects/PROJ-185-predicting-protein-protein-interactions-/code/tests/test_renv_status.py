"""Unit test for R environment status using renv.

This test invokes ``Rscript -e "renv::status()"`` and asserts that the
command exits with a zero status code. Any non‑zero exit (including errors
from missing R installation) will cause the test to fail, ensuring the
R environment is correctly initialised and the ``renv`` package is
functional.
"""

import subprocess

def test_renv_status():
    """Run ``renv::status()`` via Rscript and check for successful execution."""
    result = subprocess.run(
        ["Rscript", "-e", "renv::status()"],
        capture_output=True,
        text=True,
    )
    # Provide detailed output on failure for easier debugging.
    assert result.returncode == 0, (
        f"renv status failed with exit code {result.returncode}\\n"
        f"STDOUT:\\n{result.stdout}\\nSTDERR:\\n{result.stderr}"
    )
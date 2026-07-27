"""
test_renv_status.py

Ensures that the ``renv`` environment reports a healthy status after
initialisation.  The test runs the R command ``renv::status()`` and expects
an exit code of ``0``.
"""

import subprocess

def test_renv_status():
    """Running ``renv::status()`` must succeed (exit code 0)."""
    result = subprocess.run(
        ["Rscript", "-e", "renv::status()"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"renv status failed: {result.stderr}"

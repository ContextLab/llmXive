"""
test_renv_status_unit.py

A minimal unit‑test that directly checks the exit code of the ``renv``
status command.
"""

import subprocess

def test_renv_status_exit_code():
    """The ``renv::status()`` command should exit with status 0."""
    completed = subprocess.run(["Rscript", "-e", "renv::status()"])
    assert completed.returncode == 0

"""
Integration test that runs ``Rscript -e "renv::status()"`` to ensure the
``renv`` infrastructure is functional after ``initialize_renv``.
"""

import subprocess
from pathlib import Path

import pytest

from init_r_environment import initialize_renv

@pytest.fixture(scope="session")
def renv_initialized(tmp_path_factory):
    """
    Initialise the R environment once for the whole session.
    """
    initialize_renv()
    # Return the repository root for the caller.
    return Path(__file__).resolve().parents[2]

def test_renv_status(renv_initialized):
    """
    ``renv::status()`` should exit with status 0 when the lock file is
    present and the environment is consistent.
    """
    repo_root = renv_initialized
    result = subprocess.run(
        ["Rscript", "-e", "renv::status()"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    # ``renv::status()`` prints a summary to stdout; we only care that it
    # exits cleanly.
    assert result.returncode == 0, f"renv status failed: {result.stderr}"
    # Optional sanity check – the output should contain the word "OK".
    assert "OK" in result.stdout or "up‑to‑date" in result.stdout
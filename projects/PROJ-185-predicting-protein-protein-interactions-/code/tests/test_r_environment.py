"""
test_r_environment.py

Unit‑tests for the R environment initialisation utilities defined in
``init_r_environment.py``.  The tests exercise:

* ``run_command`` – success and failure handling.
* ``initialize_renv`` – creation of a ``renv.lock`` file.
* Basic verification that the generated lockfile is valid JSON.
"""

import subprocess
import json
from pathlib import Path

import pytest

# The functions under test live in the sibling module.
from init_r_environment import run_command, initialize_renv, install_bioc_packages

# ----------------------------------------------------------------------
# run_command tests
# ----------------------------------------------------------------------
def test_run_command_success():
    """A simple command that succeeds should return a CompletedProcess."""
    result = run_command(["echo", "hello"])
    assert result.returncode == 0
    # ``echo`` adds a trailing newline.
    assert result.stdout.strip() == "hello"

def test_run_command_failure():
    """A failing command must raise ``CalledProcessError``."""
    with pytest.raises(subprocess.CalledProcessError):
        run_command(["false"])

# ----------------------------------------------------------------------
# renv initialisation tests
# ----------------------------------------------------------------------
def test_initialize_renv_integration(tmp_path, monkeypatch):
    """
    Initialise ``renv`` in a temporary directory and verify that a
    ``renv.lock`` file appears.
    """
    # Switch to a temporary clean directory so the real repository is not
    # polluted.
    monkeypatch.chdir(tmp_path)

    initialize_renv()

    lock_file = tmp_path / "renv.lock"
    assert lock_file.is_file(), "renv.lock was not created"

def test_lockfile_verification(tmp_path, monkeypatch):
    """
    After ``initialize_renv`` the lockfile should be valid JSON.
    """
    monkeypatch.chdir(tmp_path)
    initialize_renv()

    lock_path = tmp_path / "renv.lock"
    with lock_path.open() as fp:
        data = json.load(fp)

    # ``renv`` uses a top‑level ``Packages`` key (capitalised) in the
    # lockfile format.
    assert "Packages" in data or "packages" in data

# ----------------------------------------------------------------------
# Bioconductor installation test (lightweight – only checks that the
# command runs without error).  The actual package versions are verified
# in ``tests/test_renv_lock.py``.
# ----------------------------------------------------------------------
def test_install_bioc_packages(tmp_path, monkeypatch):
    """
    Run the Bioconductor installation in an isolated directory.
    The test only asserts that the command completes; detailed package
    verification is performed elsewhere.
    """
    monkeypatch.chdir(tmp_path)
    # ``initialize_renv`` creates the lockfile required before installing
    # packages.
    initialize_renv()
    install_bioc_packages()
    # Verify that the lockfile still exists after package installation.
    assert (tmp_path / "renv.lock").is_file()

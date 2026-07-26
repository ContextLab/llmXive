import json
import shutil
import subprocess
from pathlib import Path

import pytest

# Import the functions we are testing
from init_r_environment import run_command, initialize_renv, main

def test_run_command_success(tmp_path):
    """A simple command that should succeed."""
    result = run_command(["python", "--version"], cwd=tmp_path)
    assert result.returncode == 0
    # The version string appears in stdout or stderr depending on Python version
    assert "Python" in (result.stdout + result.stderr)

def test_run_command_failure(tmp_path):
    """A command that intentionally fails should raise CalledProcessError."""
    with pytest.raises(subprocess.CalledProcessError):
        run_command(
            ["python", "-c", "import sys; sys.exit(1)"],
            cwd=tmp_path,
        )

@pytest.mark.skipif(
    shutil.which("Rscript") is None,
    reason="Rscript executable not found in PATH – skipping R integration tests",
)
def test_initialize_renv_integration(tmp_path):
    """
    Initialise an renv environment in a temporary directory and verify that
    ``renv.lock`` is created.
    """
    initialize_renv(tmp_path)

    lock_path = tmp_path / "renv.lock"
    assert lock_path.is_file(), "renv.lock should exist after initialise_renv"

@pytest.mark.skipif(
    shutil.which("Rscript") is None,
    reason="Rscript executable not found in PATH – skipping R lockfile validation",
)
def test_lockfile_verification(tmp_path):
    """
    After initialisation, ``renv.lock`` must be valid JSON and contain the
    required Bioconductor packages with recorded versions.
    """
    initialize_renv(tmp_path)
    lock_path = tmp_path / "renv.lock"
    assert lock_path.is_file(), "renv.lock missing"

    # Load the lockfile – it is JSON formatted
    with lock_path.open("r", encoding="utf-8") as f:
        lock_data = json.load(f)

    # The lockfile should contain a top‑level ``Packages`` key
    assert "Packages" in lock_data, "renv.lock missing 'Packages' section"

    packages = lock_data["Packages"]
    required = {
        "DESeq2",
        "org.At.tair.db",
        "biomaRt",
        "sva",
        "GEOquery",
    }
    missing = required - set(packages.keys())
    assert not missing, f"Missing packages in renv.lock: {missing}"

    # Ensure each recorded package entry has a Version field
    for pkg in required:
        assert "Version" in packages[pkg], f"Package {pkg} missing Version in lockfile"

@pytest.mark.skipif(
    shutil.which("Rscript") is None,
    reason="Rscript executable not found in PATH – skipping renv status test",
)
def test_renv_status(tmp_path):
    """
    ``renv::status()`` should exit with code 0 when the environment is up‑to‑date.
    """
    initialize_renv(tmp_path)
    result = subprocess.run(
        ["Rscript", "-e", "renv::status()"],
        cwd=tmp_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    # A non‑zero exit indicates a problem; the test should fail in that case.
    assert result.returncode == 0, (
        f"renv::status() returned non‑zero exit code {result.returncode}\\n"
        f"stdout: {result.stdout}\\nstderr: {result.stderr}"
    )

def test_main_executes_without_error(monkeypatch, tmp_path):
    """
    Verify that ``main()`` runs without raising an exception when R is available.
    If R is not installed the test is skipped.
    """
    if shutil.which("Rscript") is None:
        pytest.skip("Rscript not available – cannot test main()")
    # Change working directory to a temporary path for isolation
    monkeypatch.chdir(tmp_path)
    # ``main`` should create an ``renv.lock`` file
    main()
    assert (tmp_path / "renv.lock").exists()
"""
Unit tests for the ``renv.lock`` generation script.

The tests are intentionally lightweight: they only verify that the
``renv.lock`` file exists, is valid JSON, and that it records a version
for each of the required packages.  The heavy lifting (actual R
installation) is performed by ``init_r_environment.initialize_renv``.
"""

import json
import os
from pathlib import Path

import pytest

# The script under test lives one level up from the ``tests`` package.
from init_r_environment import initialize_renv

@pytest.fixture(scope="session")
def lock_file(tmp_path_factory):
    """
    Ensure a fresh ``renv.lock`` is generated for the test session.
    The file is created in the repository root (as the script expects)
    and the path is yielded to the individual tests.
    """
    # Run the initialization – this will create ``renv.lock`` at the
    # repository root.
    initialize_renv()
    repo_root = Path(__file__).resolve().parents[2]  # project root
    lock_path = repo_root / "renv.lock"
    assert lock_path.is_file(), "renv.lock was not created"
    return lock_path

def test_renv_lock_exists(lock_file):
    """The lock file must exist after ``initialize_renv``."""
    assert lock_file.is_file()

def test_renv_lock_is_valid_json(lock_file):
    """The lock file must be parseable as JSON."""
    with lock_file.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    # Basic sanity check – top‑level must be a dict with a ``Packages`` key.
    assert isinstance(data, dict)
    assert "Packages" in data
    assert isinstance(data["Packages"], dict)

def test_renv_lock_records_package_versions(lock_file):
    """
    Verify that each required package appears in the lock file with a
    ``Version`` field.  The list mirrors the packages installed in
    ``initialize_renv``.
    """
    required = {
        "DESeq2",
        "org.At.tair.db",
        "biomaRt",
        "sva",
        "GEOquery",
    }
    with lock_file.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    packages = data.get("Packages", {})
    missing = required - packages.keys()
    assert not missing, f"Missing packages in renv.lock: {missing}"

    # Ensure each entry includes a version string.
    for pkg in required:
        version = packages[pkg].get("Version")
        assert isinstance(version, str) and version, f"Package {pkg} missing version"

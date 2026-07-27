"""
test_renv_lock.py

Checks that the ``renv.lock`` file created by ``initialize_renv`` exists,
can be parsed as JSON, and contains entries for the required Bioconductor
packages.
"""

import json
from pathlib import Path

REQUIRED_PACKAGES = {
    "DESeq2",
    "org.At.tair.db",
    "biomaRt",
    "sva",
    "GEOquery",
}

def test_renv_lock_exists():
    """The lockfile must be present in the project root."""
    assert Path("renv.lock").is_file(), "renv.lock does not exist"

def test_renv_lock_is_valid_json():
    """The lockfile must be valid JSON."""
    with Path("renv.lock").open() as fp:
        json.load(fp)  # will raise if invalid

def test_renv_lock_records_package_versions():
    """
    The lockfile should list at least one of the required Bioconductor
    packages and include a version field for each listed package.
    """
    with Path("renv.lock").open() as fp:
        data = json.load(fp)

    # ``renv`` stores package metadata under a top‑level ``Packages`` key.
    packages = data.get("Packages") or data.get("packages")
    assert isinstance(packages, dict), "Packages section missing in renv.lock"

    # Identify which of the required packages are present.
    found = [pkg for pkg in REQUIRED_PACKAGES if pkg in packages]
    assert found, f"None of the required packages {REQUIRED_PACKAGES} found in renv.lock"

    # Verify that each found package entry contains a version string.
    for pkg in found:
        pkg_info = packages[pkg]
        assert "Version" in pkg_info or "version" in pkg_info, f"Version missing for {pkg}"

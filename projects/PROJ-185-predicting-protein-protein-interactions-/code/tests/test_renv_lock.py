import json
import os
from pathlib import Path
import pytest

RENV_LOCK_PATH = Path(__file__).parent.parent / "renv.lock"

REQUIRED_PACKAGES = [
    "DESeq2",
    "org.At.tair.db",
    "biomaRt",
    "sva",
    "GEOquery"
]

def test_renv_lock_exists():
    assert RENV_LOCK_PATH.exists(), "renv.lock file must exist in code/ directory"

def test_renv_lock_is_valid_json():
    try:
        with open(RENV_LOCK_PATH, "r") as f:
            data = json.load(f)
        assert isinstance(data, dict), "renv.lock must be a JSON object"
    except json.JSONDecodeError as e:
        pytest.fail(f"renv.lock is not valid JSON: {e}")

def test_renv_lock_records_package_versions():
    with open(RENV_LOCK_PATH, "r") as f:
        data = json.load(f)

    packages = data.get("Packages", {})
    assert packages, "Packages section must not be empty"

    for pkg in REQUIRED_PACKAGES:
        assert pkg in packages, f"Required package {pkg} not found in renv.lock"
        assert "Version" in packages[pkg], f"Package {pkg} missing Version field"
        assert packages[pkg]["Version"], f"Package {pkg} has empty Version"
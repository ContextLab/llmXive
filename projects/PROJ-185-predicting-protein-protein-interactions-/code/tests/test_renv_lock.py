import json
from pathlib import Path

import pytest

# Path to the renv lockfile at the repository root
RENV_LOCK_PATH = Path("renv.lock")


def _load_lockfile():
    """Helper to load the renv.lock JSON content."""
    with RENV_LOCK_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def test_renv_lock_exists():
    """The renv.lock file must exist after the R environment initialization."""
    assert RENV_LOCK_PATH.is_file(), (
        "renv.lock not found. Ensure that the R environment initialization "
        "script (init_r_environment) has been executed and that it successfully "
        "creates a lockfile."
    )


def test_renv_lock_is_valid_json():
    """The lockfile must be valid JSON."""
    try:
        data = _load_lockfile()
    except json.JSONDecodeError as exc:
        pytest.fail(f"renv.lock is not valid JSON: {exc}")
    assert isinstance(data, dict), "renv.lock JSON root should be a dictionary."


def test_renv_lock_records_package_versions():
    """
    The lockfile must contain a ``Packages`` section where each listed package
    records its version. At a minimum, the Bioconductor packages required by the
    project should be present.
    """
    data = _load_lockfile()
    packages = data.get("Packages")
    assert isinstance(packages, dict) and packages, (
        "renv.lock is missing a non‑empty 'Packages' mapping."
    )

    # Expected core Bioconductor packages for this project
    expected_packages = {
        "DESeq2",
        "org.At.tair.db",
        "biomaRt",
        "sva",
        "GEOquery",
    }
    missing = expected_packages - set(packages.keys())
    assert not missing, f"Missing expected packages in renv.lock: {missing}"

    for pkg_name, pkg_info in packages.items():
        assert isinstance(pkg_info, dict), (
            f"Package entry for '{pkg_name}' should be a mapping."
        )
        assert "Version" in pkg_info, (
            f"Package '{pkg_name}' does not record a 'Version' field in renv.lock."
        )
        version = pkg_info["Version"]
        assert isinstance(version, str) and version, (
            f"Package '{pkg_name}' has an invalid version string."
        )
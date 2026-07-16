"""Tests for the R environment initialization artifacts.

The test suite verifies that the `renv.lock` file produced (or bundled)
with the repository declares all Bioconductor packages required by the
project. No actual R execution is performed; the test simply inspects the
static lock file.
"""

import json
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def renv_lock_path() -> Path:
    """Return the path to the bundled renv.lock file."""
    # The lock file lives under `code/renv.lock` relative to the repository root.
    return Path(__file__).resolve().parents[2] / "code" / "renv.lock"


def test_renv_lock_exists(renv_lock_path: Path) -> None:
    """The renv.lock file must exist."""
    assert renv_lock_path.is_file(), f"Missing renv.lock at {renv_lock_path}"


def test_renv_lock_contains_required_packages(renv_lock_path: Path) -> None:
    """Ensure all required Bioconductor packages are listed in renv.lock."""
    required = {
        "DESeq2",
        "org.At.tair.db",
        "biomaRt",
        "sva",
        "GEOquery",
    }

    with renv_lock_path.open() as f:
        data = json.load(f)

    packages = set(data.get("Packages", {}).keys())
    missing = required - packages
    assert not missing, f"Missing packages in renv.lock: {sorted(missing)}"
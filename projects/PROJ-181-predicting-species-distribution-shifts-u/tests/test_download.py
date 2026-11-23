"""
Basic integration tests for the download module.

The tests are intentionally lightweight – they only verify that the
command‑line interface creates the expected files when run against a
small public dataset (e.g., a single well‑known species).  They do not
attempt to download the full WorldClim archive, because that would be
too heavyweight for the CI environment.
"""

import subprocess
import sys
from pathlib import Path

import pytest

from config import DATA_DIR, PROJECT_ROOT

@pytest.fixture(scope="module")
def temp_dir(tmp_path_factory):
    """Create a temporary directory that mimics the project data layout."""
    base = tmp_path_factory.mktemp("download_test")
    # Ensure the expected sub‑directories exist
    (base / "raw").mkdir()
    return base

def run_script(args, cwd):
    """Helper to invoke the download script."""
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "code" / "download.py")] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    return result

def test_fetch_historical_occurrences(temp_dir):
    """Download a tiny set of GBIF records and check the CSV exists."""
    species_file = temp_dir / "species.txt"
    species_file.write_text("Pica pica\n")  # European magpie – many records

    result = run_script(
        [
            "--species-list",
            str(species_file),
            "--year-range",
            "1970,1971",
        ],
        cwd=temp_dir,
    )
    assert result.returncode == 0, result.stderr

    expected_csv = temp_dir / "raw" / "occurrence_1970_1971.csv"
    assert expected_csv.is_file()
    # Very small sanity check – at least the header line should be present
    with expected_csv.open() as f:
        header = f.readline()
    assert "species" in header and "decimalLatitude" in header

def test_download_historical_climate_rasters(temp_dir):
    """Download a single historical raster and verify it is saved."""
    result = run_script(
        ["--climate", "historical"],
        cwd=temp_dir,
    )
    assert result.returncode == 0, result.stderr

    climate_dir = temp_dir / "raw" / "climate_historical"
    assert climate_dir.is_dir()
    tif_files = list(climate_dir.glob("*.tif"))
    # The script should have downloaded all 19 variables
    assert len(tif_files) == 19
    for tif in tif_files:
        assert tif.stat().st_size > 100_000  # basic sanity check

def test_download_future_climate_rasters(temp_dir):
    """Attempt to download the CMIP6 future rasters (SSP245, 2050)."""
    result = run_script(
        ["--climate", "future", "--scenario", "SSP245", "--year", "2050"],
        cwd=temp_dir,
    )
    # The public WorldClim mirror provides these files, so the script should
    # succeed.  If the remote service is unavailable the test will fail,
    # which is acceptable – it signals that the implementation needs a
    # reachable data source.
    assert result.returncode == 0, result.stderr

    future_dir = temp_dir / "raw" / "climate_future"
    assert future_dir.is_dir()
    tif_files = list(future_dir.glob("*.tif"))
    assert len(tif_files) == 19
    for tif in tif_files:
        assert tif.stat().st_size > 100_000
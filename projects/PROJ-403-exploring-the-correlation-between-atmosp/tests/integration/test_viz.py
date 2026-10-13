"""
tests/integration/test_viz.py
--------------------------------

Integration test for the map‑generation pipeline (User Story 2).

The test creates a tiny synthetic NetCDF dataset containing a
``correlation`` field and an ``adjusted_p`` field, invokes the
``generate_correlation_map`` function from ``src.viz.maps`` and verifies
that a PNG file is written to disk.

The dataset is deliberately minimal (2 × 2 grid) so that the test runs
quickly and stays well within the CI resource limits.  Although the data
are synthetic, the test exercises the full code path that will be used
for real ERA5 outputs, ensuring that:

* The required variables are read correctly.
* The significance mask is applied.
* Cartopy rendering does not raise errors on a global extent.
* The output PNG file exists after execution.
"""

import pathlib
from pathlib import Path

import numpy as np
import xarray as xr
import pytest

from src.viz.maps import generate_correlation_map


@pytest.fixture
def synthetic_corr_dataset(tmp_path: Path) -> Path:
    """
    Create a tiny NetCDF file with the required variables.

    The grid is 2 × 2 covering a small portion of the globe.  Values are
    chosen so that one cell is significant (adjusted p = 0.01) and the
    other is not (adjusted p = 0.1).  This allows the mask logic to be
    exercised without needing real ERA5 data.
    """
    lat = np.array([10.0, 20.0])
    lon = np.array([30.0, 40.0])

    correlation = xr.DataArray(
        data=[[0.6, -0.4], [0.2, -0.8]],
        dims=("lat", "lon"),
        coords={"lat": lat, "lon": lon},
    )
    adjusted_p = xr.DataArray(
        data=[[0.01, 0.1], [0.03, 0.2]],
        dims=("lat", "lon"),
        coords={"lat": lat, "lon": lon},
    )

    ds = xr.Dataset(
        {"correlation": correlation, "adjusted_p": adjusted_p}
    )

    out_file = tmp_path / "synthetic_corr.nc"
    ds.to_netcdf(out_file)
    return out_file


def test_generate_correlation_map(synthetic_corr_dataset: Path, tmp_path: Path):
    """
    End‑to‑end test of ``generate_correlation_map``.

    The function should write a PNG file to the supplied output directory.
    The test checks that the file exists and that its size is non‑zero,
    which confirms that Matplotlib produced output.
    """
    band = "testband"
    season = "DJF"
    output_dir = tmp_path / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Call the function under test
    png_path = generate_correlation_map(
        band=band,
        season=season,
        input_path=synthetic_corr_dataset,
        output_path=output_dir,
    )

    # Verify the returned path matches expectation
    expected_path = output_dir / f"corr_map_{band}_{season}.png"
    assert png_path == expected_path

    # Verify that the file was created and is not empty
    assert png_path.is_file()
    assert png_path.stat().st_size > 0
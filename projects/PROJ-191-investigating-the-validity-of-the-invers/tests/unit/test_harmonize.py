import numpy as np
import pytest
from data.models import HarmonizedDataset
from data.harmonize import convert_to_si, align_to_grid

def make_raw_dataset(sep_um, force_dyne, cov_diag=None):
    """Utility to build a ``HarmonizedDataset`` that mimics the raw (non‑SI) format."""
    if cov_diag is None:
        cov_diag = np.full_like(force_dyne, 0.01)  # arbitrary small variance
    return HarmonizedDataset(
        separation_m=sep_um,          # stored in micrometers for the test
        force_n=force_dyne,           # stored in dynes for the test
        covariance_matrix=np.diag(cov_diag),
        metadata={"id": "test_raw"},
    )

def test_convert_to_si_detection():
    # Values are clearly in dynes / micrometers (order 1e-5–1e2)
    raw_sep = np.array([200.0, 400.0])          # µm
    raw_force = np.array([1e-3, 2e-3])         # dynes
    ds = make_raw_dataset(raw_sep, raw_force)

    si_ds = convert_to_si(ds)

    # After conversion, forces should be 1e-8 N and 2e-8 N
    expected_force = raw_force * 1e-5
    expected_sep = raw_sep * 1e-6

    np.testing.assert_allclose(si_ds.force_n, expected_force, rtol=1e-12)
    np.testing.assert_allclose(si_ds.separation_m, expected_sep, rtol=1e-12)

def test_align_to_grid_overlap():
    # Two datasets with overlapping separation ranges
    ds1 = make_raw_dataset(
        sep_um=np.array([100, 200, 300]),
        force_dyne=np.array([1.0, 2.0, 3.0]),
    )
    ds2 = make_raw_dataset(
        sep_um=np.array([250, 350, 450]),
        force_dyne=np.array([2.5, 3.5, 4.5]),
    )
    # Convert both to SI first
    si1 = convert_to_si(ds1)
    si2 = convert_to_si(ds2)

    merged = align_to_grid([si1, si2], grid_resolution=1e-7)

    # The common range should be [250 µm, 300 µm] → [2.5e-4, 3.0e-4] m
    assert merged.separation_m.min() >= 250e-6
    assert merged.separation_m.max() <= 300e-6
    # There should be force values for both runs at each grid point
    # Hence the total number of points equals grid points * number of runs
    expected_grid_points = int(np.ceil((300e-6 - 250e-6) / 1e-7)) + 1
    assert merged.force_n.size == expected_grid_points * 2

def test_align_to_grid_no_overlap():
    ds1 = make_raw_dataset(
        sep_um=np.array([100, 150]),
        force_dyne=np.array([1.0, 1.5]),
    )
    ds2 = make_raw_dataset(
        sep_um=np.array([300, 350]),
        force_dyne=np.array([3.0, 3.5]),
    )
    si1 = convert_to_si(ds1)
    si2 = convert_to_si(ds2)

    merged = align_to_grid([si1, si2], grid_resolution=1e-7)

    # Expect an empty dataset because there is no overlap
    assert merged.separation_m.size == 0
    assert merged.force_n.size == 0
    assert merged.covariance_matrix.size == 0
    assert merged.metadata["source_ids"] == []
"""
Unit tests for ``src.data.preprocess``.
"""

import pathlib

import h5py
import pandas as pd
import pytest

from src.data.preprocess import preprocess


def test_preprocess_creates_outputs():
    """
    Verify that the preprocessing step creates the expected artefacts
    and that they have the correct basic shape/content.
    """
    # Run the preprocessing routine
    result = preprocess()

    # ------------------------------------------------------------------
    # 1. Verify that the HDF5 file exists and has the expected dimensions
    # ------------------------------------------------------------------
    h5_path = pathlib.Path(result["samples_h5"])
    assert h5_path.is_file(), f"HDF5 output not found at {h5_path}"

    with h5py.File(h5_path, "r") as f:
        assert "samples" in f, "Dataset 'samples' missing in HDF5 file"
        data = f["samples"]
        # Expected shape: (N_events, 200, 4)
        assert data.shape[1] == 200, "Second dimension must be 200 samples"
        assert data.shape[2] == 4, "Third dimension must be 4 parameters"

    # ------------------------------------------------------------------
    # 2. Verify that the CSV point‑estimate file exists and contains >=100 rows
    # ------------------------------------------------------------------
    csv_path = pathlib.Path(result["point_estimates_csv"])
    assert csv_path.is_file(), f"CSV output not found at {csv_path}"

    df = pd.read_csv(csv_path)
    required_columns = {
        "event_id",
        "mass_ratio",
        "effective_spin",
        "component_mass_1",
        "component_mass_2",
    }
    assert required_columns.issubset(df.columns), "CSV missing required columns"
    assert len(df) >= 100, f"Expected at least 100 valid events, got {len(df)}"

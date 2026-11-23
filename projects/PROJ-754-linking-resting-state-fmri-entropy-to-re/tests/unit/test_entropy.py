"""
Unit tests for the multiscale entropy implementation (src.analysis.entropy).

The tests create a tiny synthetic time‑series dataset (real numbers,
not mocked) and verify that:

* ``multiscale_entropy`` returns a ``pandas.Series`` with one entry per
  parcel (400 entries).
* Parcels that become too short after coarse‑graining are recorded in
  ``data/derived/invalid_parcels.csv`` and receive ``np.nan`` entropy.
* The checksum helper produces a deterministic SHA‑256 string.
"""
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from llmxive_toolkit import paths
from src.analysis.entropy import multiscale_entropy, _row_checksum

@pytest.fixture
def synthetic_timeseries():
    """Create a DataFrame with 20 time‑points and 400 parcels."""
    rng = np.random.default_rng(42)
    data = rng.random((20, 400))
    cols = [f"parcel_{i}" for i in range(400)]
    return pd.DataFrame(data, columns=cols)

def test_multiscale_entropy_returns_series(synthetic_timeseries):
    """The function should return a Series of length 400."""
    entropy_series = multiscale_entropy(synthetic_timeseries, scales=(1, 2, 3, 4, 5), m=2, r=0.15)
    assert isinstance(entropy_series, pd.Series)
    assert len(entropy_series) == 400
    # No NaNs expected because 20 points > (m+1) for all scales up to 5
    assert not entropy_series.isna().any()

def test_invalid_parcels_are_written(tmp_path, monkeypatch):
    """
    Force a situation where some parcels become invalid (e.g. very short
    series after coarse‑graining) and check that the CSV file is created.
    """
    # Create a DataFrame with only 6 time‑points – scale 5 will leave only 1 point,
    # which is insufficient for m=2 (needs at least 3 points).
    data = np.random.default_rng(0).random((6, 400))
    ts_df = pd.DataFrame(data, columns=[f"parcel_{i}" for i in range(400)])

    # Patch the paths.data function so that the CSV is written inside the temporary directory
    def temp_data(*parts):
        return Path(tmp_path, *parts)

    monkeypatch.setattr("llmxive_toolkit.paths.data", temp_data, raising=False)

    # Run entropy calculation; this should create invalid_parcels.csv
    result_series = multiscale_entropy(ts_df, scales=(1, 2, 3, 4, 5), m=2, r=0.15)

    # All parcels should be marked invalid → entropy NaN
    assert result_series.isna().all()

    invalid_csv = temp_data("derived", "invalid_parcels.csv")
    assert invalid_csv.is_file()
    invalid_df = pd.read_csv(invalid_csv)
    assert "parcel_id" in invalid_df.columns
    assert len(invalid_df) == 400  # every parcel recorded as invalid

def test_row_checksum_is_deterministic():
    """Checksum should be reproducible and depend on the values."""
    row = pd.Series({"subject_id": "subj01", "parcel_id": "parcel_0", "entropy": 1.2345})
    checksum1 = _row_checksum(row)
    checksum2 = _row_checksum(row.copy())
    assert checksum1 == checksum2
    # Changing a value changes the checksum
    row2 = row.copy()
    row2["entropy"] = 9.999
    assert _row_checksum(row2) != checksum1

"""Tests for the descriptor‑gap checker.

The test suite creates temporary feature matrices with and without missing
descriptor values and verifies that ``check_descriptor_gaps`` behaves as
expected.
"""

import pandas as pd
import pytest
from pathlib import Path

from src.utils.check_descriptor_gaps import check_descriptor_gaps, _descriptor_columns

def _make_features_df(missing: bool) -> pd.DataFrame:
    """Utility to create a minimal features DataFrame."""
    cols = _descriptor_columns() + ["formation_energy", "composition"]
    data = {
        "composition": ["BaTiO3", "SrTiO3"],
        "formation_energy": [1.2, 0.9],
    }
    # Populate all descriptor columns with dummy numeric values.
    for col in _descriptor_columns():
        data[col] = [2.0, 2.0]

    df = pd.DataFrame(data)

    if missing:
        # Introduce a NaN in one descriptor for the first row.
        df.at[0, "A_atomic_radius"] = pd.NA
    return df

def test_check_descriptor_gaps_no_missing(tmp_path: Path):
    """When no gaps exist the function should complete silently."""
    df = _make_features_df(missing=False)
    features_path = tmp_path / "features.csv"
    df.to_csv(features_path, index=False)

    # Should not raise
    check_descriptor_gaps(features_path=features_path)

    # Log file should contain the success message.
    log_path = tmp_path / "descriptor_gaps.log"
    # The function writes to the default location; we verify that the default file
    # was created and contains the expected text.
    default_log = Path("data/processed/descriptor_gaps.log")
    assert default_log.is_file()
    with default_log.open() as f:
        content = f.read()
    assert "No descriptor gaps found" in content

def test_check_descriptor_gaps_with_missing(tmp_path: Path):
    """When gaps are present the function must raise RuntimeError."""
    df = _make_features_df(missing=True)
    features_path = tmp_path / "features.csv"
    df.to_csv(features_path, index=False)

    with pytest.raises(RuntimeError) as excinfo:
        check_descriptor_gaps(features_path=features_path)

    assert "Descriptor gaps detected" in str(excinfo.value)

    # Verify that a log file was written with details about the missing column.
    default_log = Path("data/processed/descriptor_gaps.log")
    assert default_log.is_file()
    with default_log.open() as f:
        log_content = f.read()
    assert "missing A_atomic_radius" in log_content
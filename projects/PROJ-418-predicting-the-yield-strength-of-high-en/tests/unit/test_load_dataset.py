"""
Unit tests for ``code/data/load_dataset.py``.
"""

import builtins
import os
from pathlib import Path

import pytest

# Import the function under test
from data.load_dataset import load_raw_dataset


def test_load_raw_dataset_file_not_found(tmp_path, monkeypatch):
    """
    Ensure that ``load_raw_dataset`` raises ``FileNotFoundError`` when the
    expected CSV does not exist.
    """
    # Construct a path that is guaranteed not to exist.
    missing_file = tmp_path / "nonexistent_heas_raw.csv"

    # Monkey‑patch the default path inside the function by passing it
    # explicitly; this avoids any reliance on the real project data.
    with pytest.raises(FileNotFoundError) as exc_info:
        load_raw_dataset(csv_path=missing_file)

    # The exception message should contain the missing path.
    assert str(missing_file) in str(exc_info.value)


def test_load_raw_dataset_success(tmp_path, monkeypatch):
    """
    Verify that a valid CSV is loaded correctly.
    """
    # Create a minimal but valid CSV file.
    csv_content = "composition,yield_strength,unit\\nFe0.25Ni0.25Co0.25Cr0.25,500,MPa\\n"
    csv_path = tmp_path / "heas_raw.csv"
    csv_path.write_text(csv_content, encoding="utf-8")

    # Load the dataset.
    df = load_raw_dataset(csv_path=csv_path)

    # Basic sanity checks.
    assert df.shape == (1, 3)
    assert list(df.columns) == ["composition", "yield_strength", "unit"]
    assert df["yield_strength"].iloc[0] == 500


# The tests are deliberately lightweight and do not depend on the real
# dataset.  They only verify correct error handling and successful parsing
# of a minimal CSV.  Real‑world execution will use the actual file produced
# by the download step (T140).
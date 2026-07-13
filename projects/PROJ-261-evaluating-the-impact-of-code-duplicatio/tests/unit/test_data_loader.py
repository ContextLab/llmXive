"""
Unit tests for the data_loader module.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from code.data_loader import download_and_save_sample


@pytest.mark.parametrize("size", [1, 5, 10])
def test_download_and_save_sample_creates_file(tmp_path: Path, size: int):
    """The function must create a CSV file with the expected number of rows."""
    output = tmp_path / "sample.csv"
    result_path = download_and_save_sample(sample_size=size, output_path=output)
    assert result_path == output
    with result_path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    # Header + rows => rows length == size
    assert len(rows) == size
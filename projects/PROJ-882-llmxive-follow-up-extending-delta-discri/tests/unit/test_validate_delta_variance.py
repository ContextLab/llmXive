"""
Unit test for the variance validation script (T015c).

The test constructs a temporary JSON file with a known variance and
checks that the script behaves as expected:

* When the variance is above the threshold, the script exits without error.
* When the variance is below or equal to the threshold, a RuntimeError
  with the exact message ``ERR_TRIVIAL_TARGET`` is raised.
"""

import json
import tempfile
from pathlib import Path

import pytest

# Import the functions directly from the module we just created.
from code.validate_delta_variance import (
    load_coefficients,
    verify_global_variance,
)


def write_coefficients(tmp_path: Path, records):
    """
    Helper to write a JSON file compatible with ``load_coefficients``.
    """
    file_path = tmp_path / "delta_coefficients.json"
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(records, f)
    return file_path


def test_variance_above_threshold(tmp_path: Path):
    # Coefficients with variance > 1e-9
    records = [
        {"token_id": 0, "coefficient": 0.0},
        {"token_id": 1, "coefficient": 1.0},
        {"token_id": 2, "coefficient": -1.0},
    ]
    file_path = write_coefficients(tmp_path, records)

    coeffs = load_coefficients(file_path)
    # Should not raise
    verify_global_variance(coeffs)


def test_variance_below_or_equal_threshold(tmp_path: Path):
    # All coefficients identical → variance == 0
    records = [
        {"token_id": 0, "coefficient": 0.5},
        {"token_id": 1, "coefficient": 0.5},
    ]
    file_path = write_coefficients(tmp_path, records)

    coeffs = load_coefficients(file_path)

    with pytest.raises(RuntimeError) as excinfo:
        verify_global_variance(coeffs)

    assert str(excinfo.value) == "ERR_TRIVIAL_TARGET"
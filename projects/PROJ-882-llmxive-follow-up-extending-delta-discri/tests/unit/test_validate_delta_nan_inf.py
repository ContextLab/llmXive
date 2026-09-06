"""
Unit tests for the NaN/Inf validation logic in ``code.validate_delta_nan_inf``.
"""
import json
import tempfile
from pathlib import Path

import pytest

# Import the functions we need to test
from code.validate_delta_nan_inf import (
    _contains_invalid_number,
    validate_no_nan_inf,
    load_json_file,
)


def write_json_to_temp(data) -> Path:
    """
    Helper that writes *data* to a temporary JSON file and returns the path.
    """
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    with open(tmp_file.name, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return Path(tmp_file.name)


def test_contains_invalid_number_detects_nan():
    data = {"coefficients": [1.0, float("nan"), 2.5]}
    assert _contains_invalid_number(data) is True


def test_contains_invalid_number_detects_inf():
    data = {"coefficients": [1.0, float("inf")]}
    assert _contains_invalid_number(data) is True


def test_contains_invalid_number_no_invalid():
    data = {"coefficients": [0.0, -1.2, 3.14], "metadata": {"example_id": 42}}
    assert _contains_invalid_number(data) is False


def test_validate_no_nan_inf_raises_on_invalid():
    data = {"coefficients": [float("nan")]}
    with pytest.raises(ValueError, match="NaN or Inf"):
        validate_no_nan_inf(data)


def test_validate_no_nan_inf_passes_on_valid():
    data = {"coefficients": [0.1, 0.2, 0.3]}
    # Should not raise any exception
    validate_no_nan_inf(data)


def test_load_json_file_success():
    sample = {"a": 1, "b": [2, 3]}
    path = write_json_to_temp(sample)
    loaded = load_json_file(path)
    assert loaded == sample


def test_load_json_file_not_found():
    non_existent = Path("non_existent_file.json")
    with pytest.raises(FileNotFoundError):
        load_json_file(non_existent)
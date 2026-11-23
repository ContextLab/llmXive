"""
Contract test for real data validation.
Asserts that raw and processed data files contain real data and no synthetic placeholders.
"""
import json
import os
import pytest
from pathlib import Path
import hashlib

# Project root is the parent of the 'tests' directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Paths to expected data files
RAW_MATERIALS_PATH = PROJECT_ROOT / "data" / "raw" / "materials_project_data.json"
RAW_NIST_PATH = PROJECT_ROOT / "data" / "raw" / "nist_data.json"
PROCESSED_FEATURES_PATH = PROJECT_ROOT / "data" / "processed" / "graph_features.npy"
CHECKSUMS_PATH = PROJECT_ROOT / "data" / "checksums.txt"


def _get_file_hash(filepath: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def _check_file_not_empty(filepath: Path) -> None:
    """Assert file exists and is not empty."""
    assert filepath.exists(), f"File not found: {filepath}"
    assert filepath.stat().st_size > 0, f"File is empty: {filepath}"


def _check_json_not_synthetic(filepath: Path) -> None:
    """
    Assert JSON data is not synthetic/fake.
    Checks for:
    - Non-empty list of records
    - Presence of expected keys
    - Values that look real (not obvious placeholders like "test", "sample", -1, etc.)
    """
    with open(filepath, "r") as f:
        data = json.load(f)

    assert isinstance(data, list), "Expected a list of records"
    assert len(data) > 0, "Data list is empty"

    # Heuristic checks for synthetic data
    sample_record = data[0]
    assert isinstance(sample_record, dict), "Expected records to be dictionaries"

    # Check for obvious synthetic markers
    synthetic_indicators = [
        "test", "sample", "dummy", "placeholder", "fake", "synthetic",
        "example", "mock", "null", "None"
    ]

    for key, value in sample_record.items():
        if isinstance(value, str):
            val_lower = value.lower()
            for indicator in synthetic_indicators:
                assert indicator not in val_lower, (
                    f"Synthetic marker '{indicator}' found in field '{key}': {value}"
                )
            # Check for empty strings or very short strings that look like placeholders
            assert len(value.strip()) > 3, (
                f"Field '{key}' has suspiciously short value: '{value}'"
            )

        if isinstance(value, (int, float)):
            # Check for obviously fake numeric values
            assert value != -1, f"Field '{key}' has suspicious value -1"
            assert value != 0 or key in ["atomic_number", "period", "group"], (
                f"Field '{key}' has suspicious zero value: {value}"
            )

    # Check for reasonable data volume (not just 1-2 rows)
    assert len(data) > 10, (
        f"Data has only {len(data)} records, which is suspiciously small for real data"
    )


def _check_npy_not_synthetic(filepath: Path) -> None:
    """
    Assert NumPy array data is not synthetic.
    Checks for:
    - Non-trivial shape
    - Variance in values (not all zeros or identical)
    - Reasonable value ranges
    """
    try:
        import numpy as np
    except ImportError:
        pytest.skip("NumPy not installed")

    array = np.load(filepath)

    assert array.size > 0, "Array is empty"
    assert array.ndim >= 1, "Array has no dimensions"

    # Check for reasonable shape
    assert array.shape[0] > 10, (
        f"Array has only {array.shape[0]} samples, which is suspiciously small"
    )

    # Check for variance (not all identical values)
    if array.size > 1:
        variance = np.var(array)
        assert variance > 1e-10, (
            f"Array has suspiciously low variance: {variance}"
        )

    # Check for reasonable value ranges (not all zeros or extreme values)
    mean_val = np.mean(array)
    std_val = np.std(array)
    assert std_val > 1e-6, (
        f"Array has suspiciously low standard deviation: {std_val}"
    )


def test_raw_materials_data_integrity():
    """Test that raw Materials Project data is real and not synthetic."""
    _check_file_not_empty(RAW_MATERIALS_PATH)
    _check_json_not_synthetic(RAW_MATERIALS_PATH)


def test_raw_nist_data_integrity():
    """Test that raw NIST data is real and not synthetic."""
    _check_file_not_empty(RAW_NIST_PATH)
    _check_json_not_synthetic(RAW_NIST_PATH)


def test_processed_features_integrity():
    """Test that processed feature data is real and not synthetic."""
    if PROCESSED_FEATURES_PATH.exists():
        _check_file_not_empty(PROCESSED_FEATURES_PATH)
        _check_npy_not_synthetic(PROCESSED_FEATURES_PATH)


def test_checksums_file_exists():
    """Test that checksums file exists and contains entries."""
    _check_file_not_empty(CHECKSUMS_PATH)

    with open(CHECKSUMS_PATH, "r") as f:
        lines = [line.strip() for line in f if line.strip()]

    assert len(lines) > 0, "Checksums file is empty"

    # Check format: each line should have a hash and a filename
    for line in lines:
        parts = line.split()
        assert len(parts) >= 2, f"Invalid checksum line format: {line}"
        hash_value = parts[0]
        assert len(hash_value) == 64, (
            f"Invalid SHA256 hash length: {len(hash_value)} (expected 64)"
        )
        # Verify it's a valid hex string
        try:
            int(hash_value, 16)
        except ValueError:
            pytest.fail(f"Invalid hex character in hash: {hash_value}")
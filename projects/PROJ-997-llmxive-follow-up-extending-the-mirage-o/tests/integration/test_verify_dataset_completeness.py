"""
Integration test for T015e: verify_dataset_completeness.py

Tests the logic of verifying dataset completeness against expected counts
and the minimum floor constraint.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import pandas as pd

from src.cli.verify_dataset_completeness import (
    verify_dataset_completeness,
    load_generation_metadata,
    MIN_SAMPLE_FLOOR
)


@pytest.fixture
def temp_dirs():
    """Create a temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        data_dir = tmp_path / "data" / "processed"
        data_dir.mkdir(parents=True)
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir(parents=True)
        yield tmp_path, data_dir, logs_dir


def test_verify_success_matches_metadata(temp_dirs):
    """Test when actual count matches expected count in metadata."""
    tmp_path, data_dir, logs_dir = temp_dirs
    dataset_path = data_dir / "training_sample.parquet"
    metadata_path = data_dir / "generation_metadata.json"

    # Create dummy dataset
    df = pd.DataFrame({"col1": range(500), "col2": range(500)})
    df.to_parquet(dataset_path)

    # Create metadata with matching expected count
    metadata = {"expected_count_after_skips": 500}
    with open(metadata_path, "w") as f:
        json.dump(metadata, f)

    success, message = verify_dataset_completeness(
        dataset_path, metadata_path, min_floor=300
    )

    assert success is True
    assert "matches expected count" in message


def test_verify_warning_mismatch_metadata(temp_dirs):
    """Test when actual count differs from expected count (warning, not failure)."""
    tmp_path, data_dir, logs_dir = temp_dirs
    dataset_path = data_dir / "training_sample.parquet"
    metadata_path = data_dir / "generation_metadata.json"

    # Create dummy dataset with 400 rows
    df = pd.DataFrame({"col1": range(400), "col2": range(400)})
    df.to_parquet(dataset_path)

    # Create metadata expecting 500
    metadata = {"expected_count_after_skips": 500}
    with open(metadata_path, "w") as f:
        json.dump(metadata, f)

    success, message = verify_dataset_completeness(
        dataset_path, metadata_path, min_floor=300
    )

    # Should succeed (>= 300) but warn about mismatch
    assert success is True
    assert "does not match expected count" in message


def test_verify_failure_below_floor(temp_dirs):
    """Test when count is below the minimum floor (failure)."""
    tmp_path, data_dir, logs_dir = temp_dirs
    dataset_path = data_dir / "training_sample.parquet"
    metadata_path = data_dir / "generation_metadata.json"

    # Create dummy dataset with 200 rows (below 300 floor)
    df = pd.DataFrame({"col1": range(200), "col2": range(200)})
    df.to_parquet(dataset_path)

    # Metadata says we expected 500
    metadata = {"expected_count_after_skips": 500}
    with open(metadata_path, "w") as f:
        json.dump(metadata, f)

    success, message = verify_dataset_completeness(
        dataset_path, metadata_path, min_floor=300
    )

    assert success is False
    assert "below the minimum floor" in message


def test_verify_no_metadata_file(temp_dirs):
    """Test behavior when metadata file is missing."""
    tmp_path, data_dir, logs_dir = temp_dirs
    dataset_path = data_dir / "training_sample.parquet"
    metadata_path = data_dir / "generation_metadata.json"

    # Create dummy dataset
    df = pd.DataFrame({"col1": range(400), "col2": range(400)})
    df.to_parquet(dataset_path)

    # Do NOT create metadata file

    success, message = verify_dataset_completeness(
        dataset_path, metadata_path, min_floor=300
    )

    assert success is True
    assert "No generation metadata found" in message


def test_verify_dataset_not_found(temp_dirs):
    """Test failure when dataset file is missing."""
    tmp_path, data_dir, logs_dir = temp_dirs
    dataset_path = data_dir / "training_sample.parquet"
    metadata_path = data_dir / "generation_metadata.json"

    # Do NOT create dataset file
    metadata = {"expected_count_after_skips": 500}
    with open(metadata_path, "w") as f:
        json.dump(metadata, f)

    success, message = verify_dataset_completeness(
        dataset_path, metadata_path, min_floor=300
    )

    assert success is False
    assert "Dataset file not found" in message


def test_load_metadata_invalid_json(temp_dirs):
    """Test load_generation_metadata with invalid JSON."""
    tmp_path, data_dir, logs_dir = temp_dirs
    metadata_path = data_dir / "generation_metadata.json"

    # Write invalid JSON
    with open(metadata_path, "w") as f:
        f.write("{ invalid json }")

    result = load_generation_metadata(metadata_path)
    assert result is None
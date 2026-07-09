"""
Unit tests for code/utils/data_loader.py
"""
import os
import tempfile
import pytest
import pandas as pd

from code.utils.data_loader import load_csv, save_csv


@pytest.fixture
def sample_df():
    """Create a simple sample DataFrame."""
    return pd.DataFrame({
        "id": [1, 2, 3],
        "name": ["A", "B", "C"],
        "value": [10.5, 20.1, 30.9]
    })


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


def test_save_and_load_csv_roundtrip(sample_df, temp_dir):
    """Test that saving and loading a CSV returns the original data."""
    output_path = os.path.join(temp_dir, "test_data.csv")

    # Save
    save_csv(sample_df, output_path)

    # Verify file exists
    assert os.path.exists(output_path), "Output file was not created"

    # Load
    loaded_df = load_csv(output_path)

    # Check equality
    pd.testing.assert_frame_equal(sample_df, loaded_df)


def test_load_nonexistent_file(temp_dir):
    """Test that loading a non-existent file raises FileNotFoundError."""
    bad_path = os.path.join(temp_dir, "does_not_exist.csv")

    with pytest.raises(FileNotFoundError):
        load_csv(bad_path)


def test_save_creates_parent_dirs(temp_dir):
    """Test that save_csv creates parent directories if they don't exist."""
    nested_path = os.path.join(temp_dir, "subdir1", "subdir2", "data.csv")
    sample_df = pd.DataFrame({"col": [1]})

    save_csv(sample_df, nested_path)

    assert os.path.exists(nested_path)


def test_empty_dataframe_save_load(temp_dir):
    """Test handling of an empty DataFrame."""
    empty_df = pd.DataFrame(columns=["a", "b", "c"])
    output_path = os.path.join(temp_dir, "empty.csv")

    save_csv(empty_df, output_path)
    loaded_df = load_csv(output_path)

    assert len(loaded_df) == 0
    assert list(loaded_df.columns) == ["a", "b", "c"]
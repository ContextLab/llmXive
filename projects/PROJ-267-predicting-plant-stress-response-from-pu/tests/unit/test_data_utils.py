"""
Unit tests for data loading utilities in code/utils/data_utils.py.
"""
import os
import tempfile
import pandas as pd
import pytest
from pathlib import Path

# Import the module under test
# Note: We assume the test runner sets the PYTHONPATH to the project root
from code.utils.data_utils import (
    load_csv,
    load_parquet,
    save_csv,
    save_parquet,
    detect_file_format,
    load_data,
    save_data
)
from code.utils.config import DATA_PROCESSED_PATH


@pytest.fixture
def sample_df():
    """Create a sample DataFrame for testing."""
    return pd.DataFrame({
        'id': [1, 2, 3, 4, 5],
        'name': ['A', 'B', 'C', 'D', 'E'],
        'value': [10.5, 20.3, 30.1, 40.8, 50.2],
        'category': ['X', 'Y', 'X', 'Y', 'Z']
    })


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


class TestCSVOperations:
    def test_load_csv_success(self, sample_df, temp_dir):
        """Test successful CSV loading."""
        file_path = Path(temp_dir) / "test.csv"
        sample_df.to_csv(file_path, index=False)

        loaded_df = load_csv(file_path)
        assert loaded_df.equals(sample_df)

    def test_load_csv_file_not_found(self, temp_dir):
        """Test loading a non-existent file raises FileNotFoundError."""
        file_path = Path(temp_dir) / "nonexistent.csv"
        with pytest.raises(FileNotFoundError):
            load_csv(file_path)

    def test_load_csv_empty_file(self, temp_dir):
        """Test loading an empty CSV raises ValueError."""
        file_path = Path(temp_dir) / "empty.csv"
        file_path.touch()

        with pytest.raises(ValueError, match="CSV file is empty"):
            load_csv(file_path)

    def test_save_csv(self, sample_df, temp_dir):
        """Test saving DataFrame to CSV."""
        file_path = Path(temp_dir) / "output.csv"
        save_csv(sample_df, file_path)

        assert file_path.exists()
        loaded_df = load_csv(file_path)
        assert loaded_df.equals(sample_df)


class TestParquetOperations:
    def test_load_parquet_success(self, sample_df, temp_dir):
        """Test successful Parquet loading."""
        file_path = Path(temp_dir) / "test.parquet"
        sample_df.to_parquet(file_path, index=False)

        loaded_df = load_parquet(file_path)
        # Parquet might change dtypes slightly (e.g., int64 vs int32), check equality with tolerance
        pd.testing.assert_frame_equal(loaded_df, sample_df)

    def test_load_parquet_file_not_found(self, temp_dir):
        """Test loading a non-existent Parquet file raises FileNotFoundError."""
        file_path = Path(temp_dir) / "nonexistent.parquet"
        with pytest.raises(FileNotFoundError):
            load_parquet(file_path)

    def test_save_parquet(self, sample_df, temp_dir):
        """Test saving DataFrame to Parquet."""
        file_path = Path(temp_dir) / "output.parquet"
        save_parquet(sample_df, file_path)

        assert file_path.exists()
        loaded_df = load_parquet(file_path)
        pd.testing.assert_frame_equal(loaded_df, sample_df)


class TestFormatDetection:
    def test_detect_csv(self):
        assert detect_file_format("data.csv") == 'csv'

    def test_detect_parquet(self):
        assert detect_file_format("data.parquet") == 'parquet'
        assert detect_file_format("data.pq") == 'parquet'

    def test_detect_invalid(self):
        with pytest.raises(ValueError, match="Unsupported file format"):
            detect_file_format("data.txt")


class TestGenericLoadSave:
    def test_load_data_csv(self, sample_df, temp_dir):
        """Test generic load_data with CSV."""
        file_path = Path(temp_dir) / "test.csv"
        sample_df.to_csv(file_path, index=False)
        loaded = load_data(file_path)
        assert loaded.equals(sample_df)

    def test_load_data_parquet(self, sample_df, temp_dir):
        """Test generic load_data with Parquet."""
        file_path = Path(temp_dir) / "test.parquet"
        sample_df.to_parquet(file_path, index=False)
        loaded = load_data(file_path)
        pd.testing.assert_frame_equal(loaded, sample_df)

    def test_save_data_csv(self, sample_df, temp_dir):
        """Test generic save_data with CSV."""
        file_path = Path(temp_dir) / "out.csv"
        save_data(sample_df, file_path)
        assert file_path.exists()

    def test_save_data_parquet(self, sample_df, temp_dir):
        """Test generic save_data with Parquet."""
        file_path = Path(temp_dir) / "out.parquet"
        save_data(sample_df, file_path)
        assert file_path.exists()
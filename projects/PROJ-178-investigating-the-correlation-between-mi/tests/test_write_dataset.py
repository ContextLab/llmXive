import os
import sys
import pytest
import pandas as pd
import hashlib
from pathlib import Path
import tempfile
import shutil

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.write_dataset import calculate_file_checksum, write_processed_dataset

class TestWriteDataset:
    """Tests for the write_dataset module functionality."""

    @pytest.fixture
    def sample_dataframe(self):
        """Create a sample DataFrame for testing."""
        return pd.DataFrame({
            'sample_id': ['S001', 'S002', 'S003'],
            'heteroplasmy_burden': [0.05, 0.12, 0.08],
            'age': [45, 62, 55],
            'sex': ['M', 'F', 'M'],
            'population': ['EUR', 'AFR', 'EAS']
        })

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for output files."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        # Cleanup after test
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_calculate_file_checksum(self, temp_output_dir):
        """Test that checksum calculation works correctly."""
        test_file = temp_output_dir / "test.txt"
        test_content = "Hello, World!"
        test_file.write_text(test_content)

        checksum = calculate_file_checksum(test_file)

        # Verify it's a valid hex string
        assert isinstance(checksum, str)
        assert len(checksum) == 64  # SHA256 hex length

        # Verify consistency
        checksum2 = calculate_file_checksum(test_file)
        assert checksum == checksum2

        # Verify against known value
        expected = hashlib.sha256(test_content.encode()).hexdigest()
        assert checksum == expected

    def test_calculate_file_checksum_large_file(self, temp_output_dir):
        """Test checksum calculation with a larger file."""
        test_file = temp_output_dir / "large.txt"
        large_content = "x" * 1000000  # 1MB of data
        test_file.write_text(large_content)

        checksum = calculate_file_checksum(test_file)
        assert len(checksum) == 64

    def test_write_processed_dataset_creates_file(self, sample_dataframe, temp_output_dir):
        """Test that write_processed_dataset creates the CSV file."""
        output_path = temp_output_dir / "output.csv"

        result = write_processed_dataset(sample_dataframe, output_path, generate_checksum=False)

        assert output_path.exists()
        assert result['rows'] == 3
        assert result['columns'] == 5
        assert 'sample_id' in result['column_names']

    def test_write_processed_dataset_generates_checksum(self, sample_dataframe, temp_output_dir):
        """Test that checksum file is generated when requested."""
        output_path = temp_output_dir / "output.csv"
        checksum_path = Path(str(output_path) + '.sha256')

        result = write_processed_dataset(sample_dataframe, output_path, generate_checksum=True)

        assert output_path.exists()
        assert checksum_path.exists()
        assert 'checksum' in result
        assert len(result['checksum']) == 64

        # Verify checksum content format
        checksum_content = checksum_path.read_text()
        assert result['checksum'] in checksum_content
        assert output_path.name in checksum_content

    def test_write_processed_dataset_empty_dataframe(self, temp_output_dir):
        """Test handling of empty DataFrame."""
        empty_df = pd.DataFrame()
        output_path = temp_output_dir / "empty.csv"

        # Should not raise an error in the write function itself,
        # but the caller (main) should handle this validation.
        result = write_processed_dataset(empty_df, output_path, generate_checksum=False)
        assert result['rows'] == 0

    def test_write_processed_dataset_missing_directory(self, sample_dataframe, temp_output_dir):
        """Test that missing parent directories are created."""
        nested_path = temp_output_dir / "sub" / "deep" / "output.csv"

        result = write_processed_dataset(sample_dataframe, nested_path, generate_checksum=False)

        assert nested_path.exists()
        assert result['rows'] == 3

    def test_write_processed_dataset_preserves_data(self, sample_dataframe, temp_output_dir):
        """Test that written data can be read back correctly."""
        output_path = temp_output_dir / "output.csv"

        write_processed_dataset(sample_dataframe, output_path, generate_checksum=False)

        # Read back and verify
        df_read = pd.read_csv(output_path)

        assert len(df_read) == len(sample_dataframe)
        assert list(df_read.columns) == list(sample_dataframe.columns)
        assert df_read['sample_id'].tolist() == sample_dataframe['sample_id'].tolist()
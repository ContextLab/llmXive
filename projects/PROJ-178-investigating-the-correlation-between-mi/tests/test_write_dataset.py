import os
import sys
import pytest
import pandas as pd
import tempfile
from pathlib import Path
import hashlib

# Add code to path if running directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.write_dataset import calculate_file_checksum, write_processed_dataset

class TestWriteDataset:
    """Tests for the write_dataset module."""

    def test_calculate_file_checksum(self, tmp_path):
        """Test that checksum calculation is deterministic and correct."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)

        checksum = calculate_file_checksum(test_file)
        expected = hashlib.md5(content).hexdigest()

        assert checksum == expected
        assert len(checksum) == 32  # MD5 hex length

    def test_write_processed_dataset(self, tmp_path):
        """Test writing a valid dataframe to CSV."""
        output_file = tmp_path / "output.csv"
        df = pd.DataFrame({
            'sample_id': ['S1', 'S2'],
            'age': [25, 30],
            'burden': [0.01, 0.02]
        })

        checksum = write_processed_dataset(df, output_file)

        assert output_file.exists()
        assert output_file.stat().st_size > 0
        
        # Verify content
        loaded_df = pd.read_csv(output_file)
        assert loaded_df.equals(df)
        
        # Verify checksum matches file content
        assert checksum == calculate_file_checksum(output_file)

    def test_write_empty_dataframe_raises(self, tmp_path):
        """Test that writing an empty dataframe raises ValueError."""
        output_file = tmp_path / "empty.csv"
        df = pd.DataFrame()

        with pytest.raises(ValueError, match="Input DataFrame is empty"):
            write_processed_dataset(df, output_file)

    def test_write_none_raises(self, tmp_path):
        """Test that writing None raises ValueError."""
        output_file = tmp_path / "none.csv"

        with pytest.raises(ValueError, match="Input DataFrame is empty"):
            write_processed_dataset(None, output_file)
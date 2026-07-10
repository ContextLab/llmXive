"""
Unit tests for code/data/save_dataset.py
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(project_root))

from data.save_dataset import validate_dataset, SEQUENCE_LENGTH, REQUIRED_COLUMNS

class TestSaveDatasetValidation:
    """Tests for the validate_dataset function."""

    def create_dummy_df(self, length=1000, nulls=False, wrong_seq_len=False):
        """Helper to create a valid or invalid dummy DataFrame."""
        seq = "A" * length
        if wrong_seq_len:
            seq = "A" * (length + 10)
        
        data = {
            'sequence': [seq],
            'atac_signal': [0.5] if not nulls else [np.nan],
            'h3k27ac_signal': [0.3] if not nulls else [np.nan],
            'ctcf_peak_label': [1],
            'cell_type': ['K562'],
            'chrom': ['chr1'],
            'start': [100],
            'end': [1100],
            'strand': ['+']
        }
        return pd.DataFrame(data)

    def test_valid_dataset(self):
        """Test that a valid dataset passes validation."""
        df = self.create_dummy_df()
        assert validate_dataset(df) is True

    def test_missing_columns(self):
        """Test that missing columns raise an error."""
        df = self.create_dummy_df()
        df = df.drop(columns=['atac_signal'])
        with pytest.raises(ValueError, match="Missing required columns"):
            validate_dataset(df)

    def test_wrong_sequence_length(self):
        """Test that wrong sequence length raises an error."""
        df = self.create_dummy_df(wrong_seq_len=True)
        with pytest.raises(ValueError, match="sequences with length"):
            validate_dataset(df)

    def test_null_values(self):
        """Test that null values in critical columns raise an error."""
        df = self.create_dummy_df(nulls=True)
        with pytest.raises(ValueError, match="Found null values"):
            validate_dataset(df)

class TestSaveDatasetIntegration:
    """Integration tests for saving to parquet."""

    def test_save_and_load(self):
        """Test that a dataset can be saved and loaded back correctly."""
        df = pd.DataFrame({
            'sequence': ['A' * 1000, 'C' * 1000],
            'atac_signal': [0.5, 0.6],
            'h3k27ac_signal': [0.3, 0.4],
            'ctcf_peak_label': [1, 0],
            'cell_type': ['K562', 'GM12878'],
            'chrom': ['chr1', 'chr2'],
            'start': [100, 200],
            'end': [1100, 1200],
            'strand': ['+', '-']
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.parquet"
            
            # Import the save function logic directly to avoid full main flow dependencies
            from data.save_dataset import save_unified_dataset
            save_unified_dataset(df, output_path)

            assert output_path.exists()
            
            loaded_df = pd.read_parquet(output_path)
            assert len(loaded_df) == len(df)
            assert list(loaded_df.columns) == list(df.columns)
            assert loaded_df['sequence'].iloc[0] == 'A' * 1000
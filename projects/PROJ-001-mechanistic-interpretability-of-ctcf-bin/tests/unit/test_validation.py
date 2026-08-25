"""
Unit tests for data validation logic in code/data/validate_dataset.py.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Import the functions to test
# Adjust import path based on how tests are run (e.g., PYTHONPATH)
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.validate_dataset import (
    validate_sequence_length,
    validate_no_nulls,
    validate_chromatin_alignment,
    validate_dataset,
    load_dataset
)

# Constants
SEQUENCE_LENGTH = 1000

@pytest.fixture
def valid_dataframe():
    """Creates a valid dataframe for testing."""
    data = {
        'sequence': ['A' * SEQUENCE_LENGTH] * 10,
        'atac_signal': np.random.rand(10).astype(np.float32),
        'h3k27ac_signal': np.random.rand(10).astype(np.float32),
        'h3k4me3_signal': np.random.rand(10).astype(np.float32),
        'label': [1, 0] * 5
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_parquet_file(valid_dataframe):
    """Creates a temporary parquet file from a valid dataframe."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "test_data.parquet")
        valid_dataframe.to_parquet(path)
        yield path

class TestSequenceLength:
    def test_valid_lengths(self, valid_dataframe):
        """Test that valid sequence lengths pass."""
        assert validate_sequence_length(valid_dataframe) is True

    def test_invalid_length(self):
        """Test that invalid sequence lengths raise ValueError."""
        df = pd.DataFrame({'sequence': ['A' * (SEQUENCE_LENGTH - 1)]})
        with pytest.raises(ValueError, match="Sequence length validation failed"):
            validate_sequence_length(df)

    def test_missing_column(self):
        """Test that missing 'sequence' column raises ValueError."""
        df = pd.DataFrame({'other_col': [1, 2, 3]})
        with pytest.raises(ValueError, match="Missing 'sequence' column"):
            validate_sequence_length(df)

    def test_null_sequence(self):
        """Test that null sequences raise ValueError."""
        df = pd.DataFrame({'sequence': [None] * 5})
        with pytest.raises(ValueError, match="null values"):
            validate_sequence_length(df)

class TestNoNulls:
    def test_valid_no_nulls(self, valid_dataframe):
        """Test that a dataframe with no nulls passes."""
        assert validate_no_nulls(valid_dataframe) is True

    def test_null_in_sequence(self):
        """Test that nulls in sequence raise ValueError."""
        df = pd.DataFrame({
            'sequence': ['A' * SEQUENCE_LENGTH, None],
            'atac_signal': [0.5, 0.5]
        })
        with pytest.raises(ValueError, match="null values"):
            validate_no_nulls(df)

    def test_null_in_numeric(self):
        """Test that nulls in numeric columns raise ValueError."""
        df = pd.DataFrame({
            'sequence': ['A' * SEQUENCE_LENGTH] * 2,
            'atac_signal': [0.5, np.nan]
        })
        with pytest.raises(ValueError, match="null values"):
            validate_no_nulls(df)

class TestChromatinAlignment:
    def test_valid_alignment(self, valid_dataframe):
        """Test that valid chromatin columns pass."""
        assert validate_chromatin_alignment(valid_dataframe) is True

    def test_missing_chromatin_columns(self):
        """Test that missing chromatin columns raise ValueError."""
        df = pd.DataFrame({
            'sequence': ['A' * SEQUENCE_LENGTH] * 5,
            'label': [1] * 5
        })
        with pytest.raises(ValueError, match="No chromatin signal columns found"):
            validate_chromatin_alignment(df)

    def test_null_chromatin_values(self, valid_dataframe):
        """Test that nulls in chromatin columns raise ValueError."""
        df = valid_dataframe.copy()
        df.loc[0, 'atac_signal'] = np.nan
        with pytest.raises(ValueError, match="Chromatin alignment failed"):
            validate_chromatin_alignment(df)

class TestFullValidation:
    def test_full_validation_pass(self, temp_parquet_file):
        """Test the full validation pipeline on a valid file."""
        assert validate_dataset(temp_parquet_file) is True

    def test_full_validation_fail_nulls(self):
        """Test the full validation pipeline fails on nulls."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "bad_data.parquet")
            df = pd.DataFrame({
                'sequence': ['A' * SEQUENCE_LENGTH] * 5,
                'atac_signal': [0.5] * 4 + [np.nan]
            })
            df.to_parquet(path)
            
            with pytest.raises(ValueError, match="null values"):
                validate_dataset(path)

    def test_full_validation_fail_length(self):
        """Test the full validation pipeline fails on length mismatch."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "bad_data.parquet")
            df = pd.DataFrame({
                'sequence': ['A' * (SEQUENCE_LENGTH - 10)] * 5,
                'atac_signal': [0.5] * 5
            })
            df.to_parquet(path)
            
            with pytest.raises(ValueError, match="Sequence length validation failed"):
                validate_dataset(path)
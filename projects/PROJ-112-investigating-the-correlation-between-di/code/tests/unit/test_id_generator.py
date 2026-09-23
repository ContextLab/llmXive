"""
Unit tests for the id_generator module.
"""
import pytest
import pandas as pd
import hashlib
from pathlib import Path
from src.preprocessing.id_generator import generate_sample_id, generate_sample_ids_dataframe

class TestGenerateSampleId:
    """Tests for the generate_sample_id function."""

    def test_basic_generation(self):
        """Test that a valid ID is generated for standard inputs."""
        cohort = "AGP"
        original_id = "sample_001"
        
        result = generate_sample_id(cohort, original_id)
        
        # Check format: 64 hex characters
        assert len(result) == 64
        assert all(c in '0123456789abcdef' for c in result)

    def test_deterministic(self):
        """Test that the same inputs always produce the same output."""
        cohort = "UKBB"
        original_id = "12345"
        
        result1 = generate_sample_id(cohort, original_id)
        result2 = generate_sample_id(cohort, original_id)
        
        assert result1 == result2

    def test_empty_cohort_raises(self):
        """Test that an empty cohort raises ValueError."""
        with pytest.raises(ValueError):
            generate_sample_id("", "sample_001")

    def test_empty_id_raises(self):
        """Test that an empty original_id raises ValueError."""
        with pytest.raises(ValueError):
            generate_sample_id("AGP", "")

    def test_hash_verification(self):
        """Verify the hash is actually SHA256 of the concatenated string."""
        cohort = "TEST"
        original_id = "ID99"
        raw_string = f"{cohort}_{original_id}"
        expected_hash = hashlib.sha256(raw_string.encode('utf-8')).hexdigest()
        
        result = generate_sample_id(cohort, original_id)
        assert result == expected_hash

class TestGenerateSampleIdsDataframe:
    """Tests for the generate_sample_ids_dataframe function."""

    def test_basic_dataframe_processing(self):
        """Test processing a simple DataFrame."""
        data = {
            'cohort_id': ['AGP', 'UKBB'],
            'original_id': ['A01', 'B02'],
            'value': [10, 20]
        }
        df = pd.DataFrame(data)
        
        result = generate_sample_ids_dataframe(df)
        
        assert 'sample_id' in result.columns
        assert len(result) == 2
        assert result['sample_id'].iloc[0] == generate_sample_id('AGP', 'A01')
        assert result['sample_id'].iloc[1] == generate_sample_id('UKBB', 'B02')

    def test_custom_column_names(self):
        """Test with custom column names."""
        data = {
            'my_cohort': ['AGP'],
            'my_id': ['X1'],
            'val': [1]
        }
        df = pd.DataFrame(data)
        
        result = generate_sample_ids_dataframe(
            df, 
            cohort_col='my_cohort', 
            id_col='my_id', 
            output_col='new_id'
        )
        
        assert 'new_id' in result.columns
        assert 'sample_id' not in result.columns

    def test_missing_cohort_column_raises(self):
        """Test that missing cohort column raises ValueError."""
        df = pd.DataFrame({'other_col': [1]})
        
        with pytest.raises(ValueError):
            generate_sample_ids_dataframe(df, cohort_col='missing_col')

    def test_missing_id_column_raises(self):
        """Test that missing id column raises ValueError."""
        df = pd.DataFrame({'cohort_id': ['AGP']})
        
        with pytest.raises(ValueError):
            generate_sample_ids_dataframe(df, id_col='missing_id')

    def test_original_dataframe_unchanged(self):
        """Test that the original DataFrame is not modified in place."""
        data = {'cohort_id': ['AGP'], 'original_id': ['A1']}
        df = pd.DataFrame(data)
        original_columns = list(df.columns)
        
        result = generate_sample_ids_dataframe(df)
        
        assert list(df.columns) == original_columns
        assert 'sample_id' in result.columns
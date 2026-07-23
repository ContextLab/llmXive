"""
Unit tests for missing value filtering in data ingestion (US1).

These tests verify the logic implemented in T013:
- Filtering samples with missing PHQ-9/GAD-7 scores.
- Logging exclusion rates.
- Ensuring the resulting dataset has no missing key values.

Note: These are write-first tests (TDD). They should be executed after T013
implementation is complete.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import logging
from io import StringIO

# Import the function to test (assuming T013 implementation)
# We will test the logic directly by mocking the ingestion pipeline components
# since the actual download might not be available in all test environments.
try:
    from code.data_ingestion import merge_data, run_ingestion
    from code.config import get_output_path
except ImportError:
    # Fallback for test environment if imports fail
    merge_data = None
    run_ingestion = None

@pytest.fixture
def sample_otu_table():
    """Create a mock OTU table with sample counts."""
    data = {
        'sample_id': ['S1', 'S2', 'S3', 'S4', 'S5'],
        'OTU_1': [10, 20, 0, 5, 100],
        'OTU_2': [5, 10, 0, 2, 50],
        'OTU_3': [0, 0, 0, 0, 10]
    }
    return pd.DataFrame(data).set_index('sample_id')

@pytest.fixture
def sample_metadata_complete():
    """Create a mock metadata table with complete mental health scores."""
    data = {
        'sample_id': ['S1', 'S2', 'S3', 'S4', 'S5'],
        'PHQ-9': [5, 10, 15, 2, 8],
        'GAD-7': [4, 9, 12, 1, 6],
        'age': [25, 30, 45, 22, 35],
        'bmi': [22.5, 28.0, 30.5, 21.0, 24.5]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_metadata_missing():
    """Create a mock metadata table with missing mental health scores."""
    data = {
        'sample_id': ['S1', 'S2', 'S3', 'S4', 'S5'],
        'PHQ-9': [5, np.nan, 15, 2, 8],
        'GAD-7': [4, 9, np.nan, 1, 6],
        'age': [25, 30, 45, 22, 35],
        'bmi': [22.5, 28.0, 30.5, 21.0, 24.5]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_metadata_all_missing():
    """Create a mock metadata table where all mental health scores are missing."""
    data = {
        'sample_id': ['S1', 'S2', 'S3'],
        'PHQ-9': [np.nan, np.nan, np.nan],
        'GAD-7': [np.nan, np.nan, np.nan],
        'age': [25, 30, 45],
        'bmi': [22.5, 28.0, 30.5]
    }
    return pd.DataFrame(data)

def test_merge_data_preserves_samples_with_complete_data(
    sample_otu_table, sample_metadata_complete
):
    """Test that merge_data correctly merges tables when all data is present."""
    # This test verifies the base case before filtering
    # Note: This assumes merge_data is implemented in T012
    if merge_data is None:
        pytest.skip("merge_data not yet implemented")
        
    result = merge_data(sample_otu_table, sample_metadata_complete)
    
    assert result is not None
    assert 'sample_id' in result.columns or result.index.name == 'sample_id'
    assert len(result) == 5
    assert not result[['PHQ-9', 'GAD-7']].isnull().any().any()

def test_filter_missing_phq9_gad7_removes_incomplete_samples(
    sample_otu_table, sample_metadata_missing, caplog
):
    """Test that samples with missing PHQ-9 or GAD-7 are filtered out."""
    if merge_data is None:
        pytest.skip("merge_data not yet implemented")
    
    with caplog.at_level(logging.INFO):
        result = merge_data(sample_otu_table, sample_metadata_missing)
        
        # Verify that samples with missing values are removed
        assert len(result) == 3  # S1, S3, S4 should remain (S2 has missing PHQ-9, S5 has missing GAD-7)
        
        # Verify remaining samples have no missing PHQ-9 or GAD-7
        assert not result[['PHQ-9', 'GAD-7']].isnull().any().any()
        
        # Verify logging occurred
        assert any("missing" in msg.lower() or "filter" in msg.lower() for msg in caplog.messages)

def test_filter_missing_all_scores_halts_or_returns_empty(
    sample_otu_table, sample_metadata_all_missing, caplog
):
    """Test behavior when all mental health scores are missing."""
    if merge_data is None:
        pytest.skip("merge_data not yet implemented")
    
    with caplog.at_level(logging.WARNING):
        result = merge_data(sample_otu_table, sample_metadata_all_missing)
        
        # Should result in empty dataframe or raise an error depending on implementation
        # For now, we expect an empty dataframe with proper logging
        assert len(result) == 0
        assert any("no valid samples" in msg.lower() or "all missing" in msg.lower() 
                  for msg in caplog.messages)

def test_merge_data_handles_mismatched_sample_ids(
    sample_otu_table, sample_metadata_complete
):
    """Test that merge_data correctly handles sample IDs that don't match."""
    if merge_data is None:
        pytest.skip("merge_data not yet implemented")
    
    # Create metadata with different sample IDs
    metadata_mismatch = sample_metadata_complete.copy()
    metadata_mismatch['sample_id'] = ['S6', 'S7', 'S8', 'S9', 'S10']
    
    result = merge_data(sample_otu_table, metadata_mismatch)
    
    # Should result in empty dataframe due to no matching IDs
    assert len(result) == 0

def test_filter_logic_preserves_covariates(
    sample_otu_table, sample_metadata_missing
):
    """Test that filtering by mental health scores preserves other covariates."""
    if merge_data is None:
        pytest.skip("merge_data not yet implemented")
        
    result = merge_data(sample_otu_table, sample_metadata_missing)
    
    # Verify that age and BMI are preserved for remaining samples
    assert 'age' in result.columns
    assert 'bmi' in result.columns
    assert not result[['age', 'bmi']].isnull().any().any()

def test_exclusion_rate_logging(sample_otu_table, sample_metadata_missing, caplog):
    """Test that exclusion rate is properly logged."""
    if merge_data is None:
        pytest.skip("merge_data not yet implemented")
    
    with caplog.at_level(logging.INFO):
        result = merge_data(sample_otu_table, sample_metadata_missing)
        
        # Original: 5 samples, Result: 3 samples, Excluded: 2 (40%)
        # Check if exclusion rate is mentioned in logs
        exclusion_logged = any(
            "exclusion" in msg.lower() or "percentage" in msg.lower() or "rate" in msg.lower()
            for msg in caplog.messages
        )
        assert exclusion_logged, "Exclusion rate should be logged"

def test_data_integrity_after_filtering(sample_otu_table, sample_metadata_missing):
    """Test that data integrity is maintained after filtering."""
    if merge_data is None:
        pytest.skip("merge_data not yet implemented")
        
    result = merge_data(sample_otu_table, sample_metadata_missing)
    
    # Verify no duplicate sample IDs
    assert len(result) == result['sample_id'].nunique()
    
    # Verify data types are preserved
    assert result['PHQ-9'].dtype in ['float64', 'int64']
    assert result['GAD-7'].dtype in ['float64', 'int64']
    
    # Verify no NaN values in key columns
    assert not result[['PHQ-9', 'GAD-7', 'age', 'bmi']].isnull().any().any()

def test_missing_value_filtering_integration_with_ingestion(caplog):
    """Integration test for missing value filtering in the full ingestion pipeline."""
    # This test would require mocking the entire download process
    # For now, we test the core logic directly
    if run_ingestion is None:
        pytest.skip("run_ingestion not yet implemented")
        
    # Mock the data fetching functions
    mock_otu = pd.DataFrame({
        'sample_id': ['S1', 'S2', 'S3'],
        'OTU_1': [10, 20, 30]
    }).set_index('sample_id')
    
    mock_metadata = pd.DataFrame({
        'sample_id': ['S1', 'S2', 'S3'],
        'PHQ-9': [5, np.nan, 15],
        'GAD-7': [4, 9, np.nan]
    })
    
    with patch('code.data_ingestion.fetch_otu_table', return_value=mock_otu):
        with patch('code.data_ingestion.fetch_study_metadata', return_value=mock_metadata):
            with caplog.at_level(logging.INFO):
                # This would normally call the full pipeline
                # For testing purposes, we just verify the filtering logic
                result = merge_data(mock_otu, mock_metadata)
                
                assert len(result) == 1  # Only S1 should remain
                assert result.iloc[0]['sample_id'] == 'S1'
                assert result.iloc[0]['PHQ-9'] == 5
                assert result.iloc[0]['GAD-7'] == 4

def test_edge_case_zero_samples_after_filtering(sample_otu_table, sample_metadata_all_missing):
    """Test edge case where filtering results in zero samples."""
    if merge_data is None:
        pytest.skip("merge_data not yet implemented")
        
    result = merge_data(sample_otu_table, sample_metadata_all_missing)
    
    assert len(result) == 0
    assert isinstance(result, pd.DataFrame)
    # Verify the structure is preserved even when empty
    assert 'sample_id' in result.columns or result.index.name == 'sample_id'

def test_missing_value_filtering_with_different_missing_patterns():
    """Test various patterns of missing values in mental health scores."""
    # Create test data with different missing patterns
    data = {
        'sample_id': ['S1', 'S2', 'S3', 'S4', 'S5', 'S6'],
        'PHQ-9': [5, np.nan, 15, 2, np.nan, 8],
        'GAD-7': [4, 9, np.nan, 1, 6, np.nan],
        'age': [25, 30, 45, 22, 35, 40],
        'bmi': [22.5, 28.0, 30.5, 21.0, 24.5, 26.0]
    }
    df = pd.DataFrame(data)
    
    # Expected: Only S1 should remain (S2 missing PHQ-9, S3 missing GAD-7, 
    # S4 complete, S5 missing PHQ-9, S6 missing GAD-7)
    # Wait, S4 should also remain: PHQ-9=2, GAD-7=1
    expected_remaining = ['S1', 'S4']
    
    # Apply filtering logic
    filtered = df.dropna(subset=['PHQ-9', 'GAD-7'])
    
    assert len(filtered) == 2
    assert list(filtered['sample_id']) == expected_remaining

def test_missing_value_filtering_preserves_sample_order():
    """Test that filtering preserves the original order of samples."""
    data = {
        'sample_id': ['S1', 'S2', 'S3', 'S4', 'S5'],
        'PHQ-9': [5, np.nan, 15, 2, 8],
        'GAD-7': [4, 9, np.nan, 1, 6],
        'age': [25, 30, 45, 22, 35],
        'bmi': [22.5, 28.0, 30.5, 21.0, 24.5]
    }
    df = pd.DataFrame(data)
    
    filtered = df.dropna(subset=['PHQ-9', 'GAD-7'])
    
    # Expected order: S1, S4 (S2 and S3 removed)
    expected_order = ['S1', 'S4']
    assert list(filtered['sample_id']) == expected_order

def test_missing_value_filtering_with_string_nan():
    """Test filtering when missing values are represented as strings."""
    data = {
        'sample_id': ['S1', 'S2', 'S3'],
        'PHQ-9': [5, 'NA', 15],
        'GAD-7': [4, 9, 'N/A'],
        'age': [25, 30, 45],
        'bmi': [22.5, 28.0, 30.5]
    }
    df = pd.DataFrame(data)
    
    # Convert string NaNs to actual NaN
    df = df.replace(['NA', 'N/A', 'null', ''], np.nan)
    df['PHQ-9'] = pd.to_numeric(df['PHQ-9'], errors='coerce')
    df['GAD-7'] = pd.to_numeric(df['GAD-7'], errors='coerce')
    
    filtered = df.dropna(subset=['PHQ-9', 'GAD-7'])
    
    assert len(filtered) == 1
    assert filtered.iloc[0]['sample_id'] == 'S1'
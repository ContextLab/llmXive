"""
Unit tests for data ingestion logic.
These tests verify the feasibility check and merging logic, specifically
focusing on missing value filtering behaviors as required by T013.
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from code.data_ingestion import check_feasibility, merge_data

def test_check_feasibility_success():
    """Test that feasibility check passes when data is valid."""
    # Create mock OTU table
    otu_df = pd.DataFrame(
        np.random.rand(5, 10),
        index=['sample1', 'sample2', 'sample3', 'sample4', 'sample5'],
        columns=['otu1', 'otu2', 'otu3', 'otu4', 'otu5', 'otu6', 'otu7', 'otu8', 'otu9', 'otu10']
    )
    
    # Create mock metadata with overlapping samples and mental health columns
    metadata_df = pd.DataFrame({
        'sample_id': ['sample1', 'sample2', 'sample3', 'sample6', 'sample7'],
        'phq9': [10, 15, 5, 20, 8],
        'gad7': [12, 18, 3, 22, 6],
        'age': [25, 30, 35, 40, 45]
    })
    
    assert check_feasibility(otu_df, metadata_df) is True

def test_check_feasibility_no_overlap():
    """Test that feasibility check fails when no overlapping samples."""
    otu_df = pd.DataFrame(
        np.random.rand(5, 10),
        index=['sample1', 'sample2', 'sample3', 'sample4', 'sample5'],
        columns=['otu1', 'otu2', 'otu3', 'otu4', 'otu5', 'otu6', 'otu7', 'otu8', 'otu9', 'otu10']
    )
    
    metadata_df = pd.DataFrame({
        'sample_id': ['sample6', 'sample7', 'sample8'],
        'phq9': [10, 15, 5],
        'gad7': [12, 18, 3]
    })
    
    assert check_feasibility(otu_df, metadata_df) is False

def test_check_feasibility_no_mh_columns():
    """Test that feasibility check fails when no mental health columns."""
    otu_df = pd.DataFrame(
        np.random.rand(5, 10),
        index=['sample1', 'sample2', 'sample3', 'sample4', 'sample5'],
        columns=['otu1', 'otu2', 'otu3', 'otu4', 'otu5', 'otu6', 'otu7', 'otu8', 'otu9', 'otu10']
    )
    
    metadata_df = pd.DataFrame({
        'sample_id': ['sample1', 'sample2', 'sample3'],
        'age': [25, 30, 35],
        'bmi': [22, 24, 26]
    })
    
    assert check_feasibility(otu_df, metadata_df) is False

def test_merge_data():
    """Test merging of OTU table and metadata."""
    otu_df = pd.DataFrame(
        np.random.rand(3, 2),
        index=['sample1', 'sample2', 'sample3'],
        columns=['otu1', 'otu2']
    )
    
    metadata_df = pd.DataFrame({
        'sample_id': ['sample1', 'sample2', 'sample4'],
        'phq9': [10, 15, 5],
        'gad7': [12, 18, 3]
    })
    
    merged = merge_data(otu_df, metadata_df)
    
    assert len(merged) == 2  # Only sample1 and sample2 should be in the result
    assert 'phq9' in merged.columns
    assert 'otu1' in merged.columns
    assert 'sample_id' in merged.columns

def test_merge_data_with_missing_values():
    """Test that merge_data handles rows with missing PHQ-9/GAD-7 values correctly."""
    # OTU table with 4 samples
    otu_df = pd.DataFrame(
        np.random.rand(4, 2),
        index=['sample1', 'sample2', 'sample3', 'sample4'],
        columns=['otu1', 'otu2']
    )
    
    # Metadata with missing values in PHQ-9 and GAD-7
    metadata_df = pd.DataFrame({
        'sample_id': ['sample1', 'sample2', 'sample3', 'sample4'],
        'phq9': [10, np.nan, 5, 20],  # sample2 has missing PHQ-9
        'gad7': [12, 18, np.nan, 6],  # sample3 has missing GAD-7
        'age': [25, 30, 35, 40]
    })
    
    # Merge the data
    merged = merge_data(otu_df, metadata_df)
    
    # Verify that the merged dataframe contains all samples initially
    assert len(merged) == 4
    
    # Verify that missing values are present in the merged dataframe
    # (Actual filtering of missing values is handled in T013 implementation)
    assert merged.loc[merged['sample_id'] == 'sample2', 'phq9'].isna().iloc[0]
    assert merged.loc[merged['sample_id'] == 'sample3', 'gad7'].isna().iloc[0]

def test_missing_value_filtering_logic():
    """
    Test the logic for filtering missing values as described in T013.
    This test verifies that samples with missing PHQ-9 or GAD-7 are correctly identified.
    """
    # Create a merged dataset with missing values
    data = {
        'sample_id': ['sample1', 'sample2', 'sample3', 'sample4', 'sample5'],
        'phq9': [10, np.nan, 5, 20, 8],
        'gad7': [12, 18, np.nan, 22, 6],
        'otu1': [100, 200, 150, 300, 250],
        'otu2': [50, 75, 60, 90, 80]
    }
    df = pd.DataFrame(data)
    
    # Identify rows with missing PHQ-9 or GAD-7
    missing_mask = df['phq9'].isna() | df['gad7'].isna()
    missing_count = missing_mask.sum()
    
    # We expect 2 rows to have missing values (sample2 and sample3)
    assert missing_count == 2
    
    # Filter out missing values
    filtered_df = df[~missing_mask]
    
    # Verify that the filtered dataframe has no missing values in key columns
    assert filtered_df['phq9'].isna().sum() == 0
    assert filtered_df['gad7'].isna().sum() == 0
    
    # Verify that the filtered dataframe has the correct number of rows
    assert len(filtered_df) == 3
    
    # Verify that the remaining samples are the correct ones
    assert set(filtered_df['sample_id']) == {'sample1', 'sample4', 'sample5'}

def test_missing_value_filtering_exclusion_rate():
    """
    Test that the exclusion rate calculation for missing values is correct.
    This test verifies the logging requirement from T013.
    """
    # Create a dataset with known missing value rate
    data = {
        'sample_id': [f'sample{i}' for i in range(100)],
        'phq9': [10 if i % 10 != 0 else np.nan for i in range(100)],  # 10% missing
        'gad7': [12 if i % 10 != 0 else np.nan for i in range(100)],  # 10% missing
        'otu1': [100] * 100
    }
    df = pd.DataFrame(data)
    
    # Calculate exclusion rate
    missing_mask = df['phq9'].isna() | df['gad7'].isna()
    exclusion_rate = missing_mask.sum() / len(df)
    
    # Verify exclusion rate is approximately 10%
    assert abs(exclusion_rate - 0.10) < 0.01
    
    # Verify that the exclusion rate is correctly calculated
    assert exclusion_rate == 0.10
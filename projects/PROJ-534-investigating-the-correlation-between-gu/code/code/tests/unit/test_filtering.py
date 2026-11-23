import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from code.src.data.filtering import filter_cohort, check_zero_variance

@pytest.fixture
def sample_cohort_data():
    """Create a sample dataframe matching the schema for testing."""
    np.random.seed(42)
    n = 100
    data = {
        'participant_id': [f"P{i}" for i in range(n)],
        'age': np.random.randint(20, 90, n),
        'sex': np.random.choice(['M', 'F'], n),
        'bmi': np.random.normal(25, 4, n),
        'dietary_fiber': np.random.normal(25, 5, n),
        'antibiotic_use': np.random.choice([True, False], n),
        'shannon_diversity': np.random.normal(3.5, 0.5, n),
        'cognitive_flexibility_score': np.random.normal(80, 10, n),
        'simpson_diversity': np.random.normal(0.9, 0.05, n),
        'chao1': np.random.normal(150, 20, n)
    }
    return pd.DataFrame(data)

@pytest.fixture
def cohort_with_missing():
    """Create a dataframe with missing values in covariates."""
    np.random.seed(42)
    n = 50
    data = {
        'participant_id': [f"P{i}" for i in range(n)],
        'age': np.random.randint(60, 90, n),
        'sex': np.random.choice(['M', 'F'], n),
        'bmi': [None if i % 5 == 0 else np.random.normal(25, 4) for i in range(n)],
        'dietary_fiber': np.random.normal(25, 5, n),
        'antibiotic_use': np.random.choice([True, False], n),
        'shannon_diversity': np.random.normal(3.5, 0.5, n),
        'cognitive_flexibility_score': np.random.normal(80, 10, n)
    }
    return pd.DataFrame(data)

def test_filter_cohort_age_only(sample_cohort_data):
    """Test that filtering correctly removes rows with age < 65."""
    # Add some young people
    young_data = pd.DataFrame({
        'participant_id': ['Y1', 'Y2', 'Y3'],
        'age': [20, 30, 40],
        'sex': ['M', 'F', 'M'],
        'bmi': [25.0, 26.0, 24.0],
        'dietary_fiber': [25.0, 25.0, 25.0],
        'antibiotic_use': [False, True, False],
        'shannon_diversity': [3.5, 3.6, 3.4],
        'cognitive_flexibility_score': [80.0, 81.0, 79.0]
    })
    combined_df = pd.concat([sample_cohort_data, young_data], ignore_index=True)
    
    filtered_df, dropped = filter_cohort(combined_df, min_age=65)
    
    # All remaining rows must be >= 65
    assert all(filtered_df['age'] >= 65)
    # We added 3 young people, so at least 3 should be dropped (plus any missing data if any)
    assert dropped >= 3

def test_filter_cohort_listwise_deletion(cohort_with_missing):
    """Test that listwise deletion removes rows with missing covariates."""
    # Ensure all rows are >= 65 to isolate missing data logic
    cohort_with_missing['age'] = 70  # Force age to be valid
    
    # Count initial rows
    initial_count = len(cohort_with_missing)
    
    # Filter
    filtered_df, dropped_count = filter_cohort(cohort_with_missing)
    
    # Verify no missing values in required columns
    required_cols = ['age', 'sex', 'bmi', 'dietary_fiber', 'antibiotic_use', 'shannon_diversity', 'cognitive_flexibility_score']
    for col in required_cols:
        assert not filtered_df[col].isna().any(), f"Column {col} still has missing values"
    
    # Verify that rows were dropped (since we introduced NAs in bmi)
    assert dropped_count > 0
    assert len(filtered_df) == initial_count - dropped_count

def test_check_zero_variance():
    """Test zero variance detection logic."""
    # Normal variance
    df_normal = pd.DataFrame({'col': [1, 2, 3, 4, 5]})
    assert not check_zero_variance(df_normal, 'col')
    
    # Zero variance
    df_const = pd.DataFrame({'col': [5, 5, 5, 5, 5]})
    assert check_zero_variance(df_const, 'col')
    
    # Missing column
    assert not check_zero_variance(df_normal, 'nonexistent')

def test_filter_cohort_handles_empty_dataframe():
    """Test filtering an empty dataframe."""
    df = pd.DataFrame({
        'age': [], 'sex': [], 'bmi': [], 'dietary_fiber': [], 
        'antibiotic_use': [], 'shannon_diversity': [], 'cognitive_flexibility_score': []
    })
    # Ensure correct types
    df['age'] = df['age'].astype(int)
    df['antibiotic_use'] = df['antibiotic_use'].astype(bool)
    
    filtered_df, dropped = filter_cohort(df)
    
    assert len(filtered_df) == 0
    assert dropped == 0
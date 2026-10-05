import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
import sys

# Add project root to path if not already present to ensure imports work
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.filtering import filter_cohort
from src.utils.config import get_processed_data_dir, get_raw_data_dir, set_seed

@pytest.fixture
def sample_cohort_data():
    """
    Generates a synthetic cohort dataframe with mixed ages,
    including rows below and above the age threshold (65).
    """
    set_seed(42)
    n = 100
    data = {
        'participant_id': [f'P{i:03d}' for i in range(n)],
        'age': np.random.randint(50, 85, size=n), # Range 50-84
        'sex': np.random.choice(['M', 'F'], size=n),
        'bmi': np.random.normal(27.0, 4.0, size=n),
        'cognitive_flexibility_score': np.random.normal(50.0, 10.0, size=n),
        'shannon_diversity': np.random.normal(3.5, 0.5, size=n),
        'simpson_diversity': np.random.normal(0.85, 0.05, size=n),
        'chao1': np.random.normal(120.0, 15.0, size=n),
        'dietary_fiber': np.random.normal(25.0, 5.0, size=n),
        'antibiotic_use': np.random.choice([True, False], size=n)
    }
    return pd.DataFrame(data)

@pytest.fixture
def cohort_with_missing():
    """
    Generates a cohort with some missing values to test listwise deletion.
    """
    set_seed(42)
    n = 50
    data = {
        'participant_id': [f'P{i:03d}' for i in range(n)],
        'age': np.random.randint(50, 85, size=n),
        'sex': np.random.choice(['M', 'F'], size=n),
        'bmi': np.random.normal(27.0, 4.0, size=n),
        'cognitive_flexibility_score': np.random.normal(50.0, 10.0, size=n),
        'shannon_diversity': np.random.normal(3.5, 0.5, size=n),
        'simpson_diversity': np.random.normal(0.85, 0.05, size=n),
        'chao1': np.random.normal(120.0, 15.0, size=n),
        'dietary_fiber': np.random.normal(25.0, 5.0, size=n),
        'antibiotic_use': np.random.choice([True, False], size=n)
    }
    df = pd.DataFrame(data)
    # Introduce missing values
    df.loc[5, 'cognitive_flexibility_score'] = np.nan
    df.loc[10, 'shannon_diversity'] = np.nan
    df.loc[15, 'age'] = np.nan
    return df

@pytest.fixture
def zero_variance_cohort():
    """
    Generates a cohort where all values for a key metric are identical.
    """
    set_seed(42)
    n = 20
    data = {
        'participant_id': [f'P{i:03d}' for i in range(n)],
        'age': [70] * n, # All same age
        'sex': ['M'] * n,
        'bmi': [25.0] * n,
        'cognitive_flexibility_score': [50.0] * n,
        'shannon_diversity': [3.0] * n, # Zero variance in diversity
        'simpson_diversity': [0.8] * n,
        'chao1': [100.0] * n,
        'dietary_fiber': [20.0] * n,
        'antibiotic_use': [False] * n
    }
    return pd.DataFrame(data)

def test_filter_age_65(sample_cohort_data):
    """
    T013: Verify output contains ONLY rows with age >= 65.
    """
    # Ensure input has mixed ages
    assert (sample_cohort_data['age'] < 65).any(), "Test fixture must contain ages < 65"
    assert (sample_cohort_data['age'] >= 65).any(), "Test fixture must contain ages >= 65"

    # Perform filtering
    filtered_df, status = filter_cohort(sample_cohort_data, age_threshold=65)

    # Assert no rows with age < 65 remain
    assert filtered_df is not None, "Filtered dataframe should not be None"
    assert len(filtered_df) > 0, "Filtered dataframe should not be empty given the fixture"
    
    # Core assertion: All ages must be >= 65
    assert (filtered_df['age'] >= 65).all(), "Filtering failed: some rows with age < 65 remain"
    
    # Verify count matches expectation
    expected_count = len(sample_cohort_data[sample_cohort_data['age'] >= 65])
    assert len(filtered_df) == expected_count, f"Expected {expected_count} rows, got {len(filtered_df)}"

def test_filter_cohort_listwise_deletion(cohort_with_missing):
    """
    Verify that participants with missing cognitive scores or covariates are excluded.
    """
    # Initial count with missing
    initial_count = len(cohort_with_missing)
    
    filtered_df, status = filter_cohort(cohort_with_missing, age_threshold=65)
    
    # Rows with missing critical fields should be dropped
    # We expect at least the rows with NaN in 'cognitive_flexibility_score' or 'shannon_diversity' to be gone
    # Note: filter_cohort handles listwise deletion for all required fields
    assert len(filtered_df) < initial_count, "Listwise deletion should have removed rows with missing values"
    
    # Verify no NaNs remain in required columns
    required_cols = ['cognitive_flexibility_score', 'shannon_diversity', 'age', 'sex', 'bmi', 'dietary_fiber', 'antibiotic_use']
    for col in required_cols:
        assert not filtered_df[col].isna().any(), f"Column {col} should not contain NaN after filtering"

def test_check_zero_variance_with_normal_data(sample_cohort_data):
    """
    Verify that normal data does not trigger zero variance flag.
    """
    from src.data.filtering import check_zero_variance
    has_zero_var, message = check_zero_variance(sample_cohort_data)
    assert not has_zero_var, "Normal data should not be flagged as zero variance"

def test_check_zero_variance_with_constant_data(zero_variance_cohort):
    """
    Verify that constant data triggers zero variance flag.
    """
    from src.data.filtering import check_zero_variance
    has_zero_var, message = check_zero_variance(zero_variance_cohort)
    assert has_zero_var, "Constant data should be flagged as zero variance"
    assert "ZERO_VARIANCE_DETECTED" in message or "zero variance" in message.lower()

def test_filter_cohort_handles_empty_dataframe():
    """
    Verify behavior when input dataframe is empty.
    """
    empty_df = pd.DataFrame(columns=['participant_id', 'age', 'sex', 'bmi', 'cognitive_flexibility_score', 'shannon_diversity'])
    filtered_df, status = filter_cohort(empty_df, age_threshold=65)
    assert filtered_df is not None
    assert len(filtered_df) == 0
    assert status.get('dropped_rows') == 0
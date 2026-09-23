import pytest
import pandas as pd
import numpy as np
import tempfile
import os
from pathlib import Path
from src.preprocessing.covariate_handler import (
    calculate_missing_ratio,
    exclude_high_missingness,
    impute_with_mice,
    process_covariates
)

@pytest.fixture
def sample_df():
    """Create a sample DataFrame with missing values."""
    return pd.DataFrame({
        'sample_id': ['S1', 'S2', 'S3', 'S4', 'S5'],
        'age': [25, 30, np.nan, 40, 35],
        'bmi': [22.5, np.nan, 24.0, 26.0, np.nan],
        'antibiotic_use': [0, 1, 0, np.nan, 1],
        'fiber_g_day': [15.0, 20.0, 18.0, 22.0, 10.0]
    })

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_calculate_missing_ratio(sample_df):
    """Test missing ratio calculation."""
    ratio = calculate_missing_ratio(sample_df, ['age', 'bmi', 'antibiotic_use'])
    assert ratio['age'] == 0.2  # 1/5
    assert ratio['bmi'] == 0.2  # 1/5
    assert ratio['antibiotic_use'] == 0.2  # 1/5

def test_exclude_high_missingness(sample_df):
    """Test exclusion of high missingness rows."""
    # S3 has 1/3 missing (33%), S4 has 1/3 missing (33%), S5 has 1/3 missing (33%)
    # With threshold 0.20, all should be excluded if we check age, bmi, antibiotic_use
    filtered_df, excluded_ids = exclude_high_missingness(
        sample_df, 
        threshold=0.20, 
        columns=['age', 'bmi', 'antibiotic_use']
    )
    # S1 and S2 have 0 and 1 missing respectively (0% and 33%)
    # Actually S2 has 1/3 missing (33%) -> excluded
    # S1 has 0/3 missing (0%) -> kept
    assert len(filtered_df) == 1
    assert 'S1' in filtered_df['sample_id'].values

def test_exclude_high_missingness_threshold_adjusted(sample_df):
    """Test exclusion with a higher threshold."""
    # With threshold 0.5, only rows with >50% missing are excluded
    # None of our rows have >50% missing in the 3 columns
    filtered_df, excluded_ids = exclude_high_missingness(
        sample_df, 
        threshold=0.50, 
        columns=['age', 'bmi', 'antibiotic_use']
    )
    assert len(filtered_df) == 5  # All kept

def test_impute_with_mice_no_missing():
    """Test imputation on data with no missing values."""
    df = pd.DataFrame({
        'age': [25, 30, 35],
        'bmi': [22.5, 24.0, 26.0]
    })
    result = impute_with_mice(df)
    assert result.equals(df)

def test_impute_with_mice_basic(sample_df):
    """Test basic MICE imputation."""
    # Select only numeric columns with missing values
    numeric_cols = ['age', 'bmi', 'antibiotic_use']
    result = impute_with_mice(sample_df, columns=numeric_cols, n_iterations=2)
    
    # Check that no NaN values remain in the imputed columns
    assert not result['age'].isna().any()
    assert not result['bmi'].isna().any()
    assert not result['antibiotic_use'].isna().any()
    
    # Check that original values are preserved where not missing
    assert result.loc[0, 'age'] == 25
    assert result.loc[0, 'bmi'] == 22.5

def test_process_covariates_full_pipeline(sample_df, temp_dir):
    """Test the full processing pipeline."""
    input_path = os.path.join(temp_dir, 'input.tsv')
    output_path = os.path.join(temp_dir, 'output.tsv')
    exclusion_log_path = os.path.join(temp_dir, 'exclusion_log.txt')
    
    # Write input
    sample_df.to_csv(input_path, sep='\t', index=False)
    
    # Run processing
    stats = process_covariates(
        input_path=input_path,
        output_path=output_path,
        exclusion_log_path=exclusion_log_path,
        threshold=0.30,  # Allow up to 30% missing
        impute=True,
        columns=['age', 'bmi', 'antibiotic_use']
    )
    
    # Verify outputs exist
    assert os.path.exists(output_path)
    assert os.path.exists(exclusion_log_path)
    
    # Verify stats
    assert stats['original_count'] == 5
    assert stats['remaining_count'] <= 5
    assert stats['imputed'] == True
    
    # Verify output has no NaN in imputed columns
    output_df = pd.read_csv(output_path, sep='\t')
    assert not output_df['age'].isna().any()
    assert not output_df['bmi'].isna().any()

def test_process_covariates_no_impute(sample_df, temp_dir):
    """Test processing without imputation."""
    input_path = os.path.join(temp_dir, 'input.tsv')
    output_path = os.path.join(temp_dir, 'output.tsv')
    exclusion_log_path = os.path.join(temp_dir, 'exclusion_log.txt')
    
    sample_df.to_csv(input_path, sep='\t', index=False)
    
    stats = process_covariates(
        input_path=input_path,
        output_path=output_path,
        exclusion_log_path=exclusion_log_path,
        threshold=0.0,  # Exclude any missing
        impute=False,
        columns=['age', 'bmi', 'antibiotic_use']
    )
    
    assert stats['imputed'] == False
    assert os.path.exists(output_path)
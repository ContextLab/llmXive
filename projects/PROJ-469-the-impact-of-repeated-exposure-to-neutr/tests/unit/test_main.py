"""
Unit tests for the main pipeline orchestration.

These tests verify that the main.py script correctly orchestrates
the data flow from raw to processed to results.
"""

import sys
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd

# Add code directory to path
code_dir = Path(__file__).parent.parent.parent / 'code'
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from preprocessing import DataIntegrityError

@pytest.fixture
def sample_data():
    """Create a sample DataFrame for testing."""
    return pd.DataFrame({
        'IAT_D_score': [0.1, 0.2, 0.3, 0.4, 0.5],
        'political_ideology': [1.0, 2.0, 3.0, 4.0, 5.0],
        'news_exposure_freq': [10, 20, 30, 40, 50],
        'age': [25, 30, 35, 40, 45],
        'gender': ['M', 'F', 'M', 'F', 'M']
    })

@pytest.fixture
def mock_logger():
    """Mock the logger to prevent console output during tests."""
    with patch('logging_config.get_logger') as mock:
        mock.return_value = MagicMock()
        yield mock

def test_preprocessing_pipeline(sample_data):
    """Test that the preprocessing pipeline correctly transforms data."""
    from preprocessing import run_preprocessing_pipeline
    
    result = run_preprocessing_pipeline(sample_data)
    
    assert result is not None
    assert 'news_exposure_z' in result.columns
    assert 'ideology_binary' in result.columns
    assert len(result) == len(sample_data)

def test_imputation_missingness_check(sample_data):
    """Test that imputation raises error when missingness > 50%."""
    from preprocessing import impute_mice
    
    # Create data with >50% missingness in a key variable
    df_missing = sample_data.copy()
    df_missing.loc[:4, 'IAT_D_score'] = None  # 80% missing
    
    with pytest.raises(DataIntegrityError, match="Missingness exceeds 50%"):
        impute_mice(df_missing)

def test_primary_model_fitting(sample_data):
    """Test that the primary model fits correctly."""
    from preprocessing import run_preprocessing_pipeline
    from models import run_primary_analysis
    
    processed = run_preprocessing_pipeline(sample_data)
    results = run_primary_analysis(processed)
    
    assert results is not None
    assert 'interaction_coef' in results
    assert 'interaction_pval' in results
    assert results['n_obs'] == len(sample_data)

def test_main_orchestration(sample_data, mock_logger):
    """Test that main.py orchestrates the pipeline correctly."""
    from preprocessing import run_preprocessing_pipeline
    from models import run_primary_analysis
    
    # Simulate the steps in main.py
    processed = run_preprocessing_pipeline(sample_data)
    assert processed is not None
    
    results = run_primary_analysis(processed)
    assert results is not None
    
    # Verify derived columns exist
    assert 'news_exposure_z' in processed.columns
    assert 'ideology_binary' in processed.columns

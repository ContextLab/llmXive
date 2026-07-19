import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code to path if running standalone
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analysis.robustness import (
    load_data, 
    filter_zero_kloc, 
    fit_negative_binomial_glm, 
    run_subsample_analysis
)

@pytest.fixture
def mock_data():
    """Create a mock dataset for testing."""
    data = {
        'url': [f'repo{i}' for i in range(100)],
        'primary_language': ['Python'] * 50 + ['JavaScript'] * 50,
        'unique_authors': np.random.randint(1, 20, 100),
        'kloc': np.random.uniform(1.0, 100.0, 100), # Ensure > 0
        'cve_count': np.random.poisson(2, 100),
        'project_age': np.random.randint(1, 10, 100),
        'release_count': np.random.randint(1, 20, 100)
    }
    return pd.DataFrame(data)

def test_filter_zero_kloc(mock_data):
    """Test that rows with kloc=0 are removed."""
    # Inject a zero kloc row
    mock_data.loc[0, 'kloc'] = 0.0
    
    filtered = filter_zero_kloc(mock_data)
    
    assert 0.0 not in filtered['kloc'].values
    assert len(filtered) == len(mock_data) - 1

def test_fit_negative_binomial_glm(mock_data):
    """Test that GLM fits successfully on valid data."""
    # Ensure kloc > 0
    mock_data = mock_data[mock_data['kloc'] > 0]
    
    result = fit_negative_binomial_glm(
        mock_data, 
        predictor_col='unique_authors',
        offset_col='kloc'
    )
    
    assert result is not None
    assert hasattr(result, 'pvalues')
    assert 'unique_authors' in result.pvalues.index

def test_run_subsample_analysis(mock_data):
    """Test subsample analysis produces expected output structure."""
    results = run_subsample_analysis(mock_data)
    
    assert isinstance(results, pd.DataFrame)
    assert not results.empty
    assert 'language' in results.columns
    assert 'p_value' in results.columns
    assert 'coefficient' in results.columns
    
    # Check that we have results for Python and JavaScript
    assert 'Python' in results['language'].values
    assert 'JavaScript' in results['language'].values
    assert len(results) == 2

def test_run_subsample_analysis_empty_input():
    """Test subsample analysis with insufficient data."""
    empty_df = pd.DataFrame(columns=['primary_language', 'unique_authors', 'kloc', 'cve_count'])
    results = run_subsample_analysis(empty_df)
    assert results.empty
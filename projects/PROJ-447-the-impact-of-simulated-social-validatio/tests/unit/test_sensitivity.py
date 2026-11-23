import pytest
import pandas as pd
import numpy as np
import json
import os
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'code'))

from analysis.sensitivity import (
    remove_outliers_iqr,
    winsorize_data,
    run_single_regression,
    run_sensitivity_analysis
)
from utils.constants import set_seed

@pytest.fixture
def sample_data():
    """Create a sample dataset for testing."""
    set_seed()
    n = 200
    data = pd.DataFrame({
        'perceived_social_validation': np.random.normal(50, 10, n),
        'self_perception_score': np.random.normal(50, 10, n),
        'age': np.random.randint(12, 19, n),
        'gender': np.random.choice(['M', 'F'], n),
        'offline_relationships': np.random.normal(50, 10, n),
        'intrinsic_traits': np.random.normal(50, 10, n)
    })
    # Add some outliers
    data.loc[0, 'perceived_social_validation'] = 200  # Extreme outlier
    data.loc[1, 'self_perception_score'] = 200
    return data

def test_remove_outliers_iqr(sample_data):
    """Test IQR outlier removal."""
    initial_len = len(sample_data)
    cleaned_data = remove_outliers_iqr(sample_data, 'perceived_social_validation', 'self_perception_score')
    
    # Should remove at least the extreme outliers
    assert len(cleaned_data) < initial_len
    assert 'perceived_social_validation' in cleaned_data.columns
    assert 'self_perception_score' in cleaned_data.columns

def test_winsorize_data(sample_data):
    """Test winsorization."""
    original_data = sample_data.copy()
    winsorized_data = winsorize_data(sample_data, 'perceived_social_validation', 'self_perception_score', limits=0.05)
    
    # Values should be clipped, not removed
    assert len(winsorized_data) == len(original_data)
    
    # Check that extreme values are clipped
    q1 = original_data['perceived_social_validation'].quantile(0.05)
    q95 = original_data['perceived_social_validation'].quantile(0.95)
    
    assert winsorized_data['perceived_social_validation'].min() >= q1
    assert winsorized_data['perceived_social_validation'].max() <= q95

def test_run_single_regression(sample_data):
    """Test single regression run."""
    confounders = ['age', 'gender', 'offline_relationships', 'intrinsic_traits']
    result = run_single_regression(
        sample_data,
        'perceived_social_validation',
        'self_perception_score',
        confounders,
        include_confounders=True
    )
    
    assert 'coefficient' in result
    assert 'p_value' in result
    assert 'status' in result
    assert result['status'] == 'success'
    assert isinstance(result['coefficient'], (int, float))
    assert isinstance(result['p_value'], (int, float))

def test_run_sensitivity_analysis(sample_data, tmp_path):
    """Test full sensitivity analysis pipeline."""
    output_path = tmp_path / 'sensitivity_analysis.json'
    results = run_sensitivity_analysis(
        sample_data,
        output_path=str(output_path)
    )
    
    # Check output file exists
    assert output_path.exists()
    
    # Check results structure
    assert isinstance(results, list)
    assert len(results) > 0  # Should have multiple runs (3 strategies * 2 confounder states)
    
    # Check each result has required keys
    for result in results:
        assert 'coefficient' in result
        assert 'p_value' in result
        assert 'outlier_strategy' in result
        assert 'confounders_included' in result
        assert 'variation_delta' in result
        
        # Verify strategies and confounder states
        assert result['outlier_strategy'] in ['none', 'IQR removal', 'winsorization']
        assert result['confounders_included'] in [True, False]
    
    # Check JSON file content
    with open(output_path, 'r') as f:
        json_data = json.load(f)
    
    assert isinstance(json_data, list)
    assert len(json_data) == len(results)
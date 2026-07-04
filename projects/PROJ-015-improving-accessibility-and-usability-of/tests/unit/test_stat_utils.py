import pytest
import pandas as pd
import numpy as np
from analysis.stat_utils import StatUtils

@pytest.fixture
def sample_data():
    """Create a mock dataset for testing difference score calculations."""
    data = {
        'session_id': ['S1', 'S1', 'S2', 'S2', 'S3', 'S3'],
        'interface_type': ['Traditional', 'Explainable', 'Traditional', 'Explainable', 'Traditional', 'Explainable'],
        'completion_time': [10.5, 9.0, 12.0, 11.0, 8.0, 7.5]
    }
    return pd.DataFrame(data)

@pytest.fixture
def stat_utils():
    return StatUtils()

def test_shapiro_wilk_normal_data(stat_utils):
    """Test Shapiro-Wilk on a normally distributed dataset."""
    # Generate normal data
    np.random.seed(42)
    normal_data = np.random.normal(loc=10, scale=2, size=50).tolist()
    
    result = stat_utils.shapiro_wilk(normal_data)
    
    assert "statistic" in result
    assert "p_value" in result
    assert isinstance(result["statistic"], float)
    assert isinstance(result["p_value"], float)
    # For normal data, p-value should typically be > 0.05 (though random)
    # We just check the function runs and returns valid structure

def test_shapiro_wilk_small_sample(stat_utils):
    """Test Shapiro-Wilk with insufficient data."""
    with pytest.raises(ValueError, match="Shapiro-Wilk test requires between 3 and 5000 samples."):
        stat_utils.shapiro_wilk([1.0, 2.0])

def test_calculate_difference_scores(stat_utils, sample_data):
    """Test calculation of difference scores."""
    diff_df = stat_utils.calculate_difference_scores(
        sample_data, 
        metric='completion_time', 
        condition_col='interface_type', 
        subject_col='session_id'
    )
    
    assert 'diff_completion_time' in diff_df.columns
    assert len(diff_df) == 3  # S1, S2, S3
    
    # Check specific values
    # S1: 10.5 - 9.0 = 1.5
    # S2: 12.0 - 11.0 = 1.0
    # S3: 8.0 - 7.5 = 0.5
    expected_diffs = [1.5, 1.0, 0.5]
    assert np.allclose(sorted(diff_df['diff_completion_time']), sorted(expected_diffs))

def test_shapiro_wilk_on_differences(stat_utils, sample_data):
    """Test full pipeline of calculating differences and running Shapiro-Wilk."""
    result = stat_utils.shapiro_wilk_on_differences(
        sample_data, 
        metric='completion_time', 
        condition_col='interface_type', 
        subject_col='session_id'
    )
    
    assert result['status'] == 'success'
    assert result['n_samples'] == 3
    assert result['metric'] == 'completion_time'
    assert result['p_value'] is not None
    assert result['statistic'] is not None
    assert isinstance(result['is_normal'], bool)

def test_shapiro_wilk_on_differences_insufficient_data(stat_utils):
    """Test pipeline with missing data for one condition."""
    data = {
        'session_id': ['S1', 'S1', 'S2'],
        'interface_type': ['Traditional', 'Explainable', 'Traditional'],
        'completion_time': [10.5, 9.0, 12.0]
    }
    df = pd.DataFrame(data)
    
    result = stat_utils.shapiro_wilk_on_differences(
        df, 
        metric='completion_time', 
        condition_col='interface_type', 
        subject_col='session_id'
    )
    
    # S2 has no Explainable data, so only S1 remains -> n=1 (insufficient)
    assert result['status'] == 'insufficient_data'
    assert result['n_samples'] == 1

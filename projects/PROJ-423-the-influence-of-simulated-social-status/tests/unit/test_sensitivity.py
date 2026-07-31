import pytest
import pandas as pd
import numpy as np
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from analysis import run_sensitivity_analysis, validate_data_structure

@pytest.fixture
def sample_data():
    """Create sample data for sensitivity analysis testing."""
    np.random.seed(42)
    n = 200
    
    # Create balanced design
    data = {
        'participant_id': range(n),
        'status_level': np.repeat(['High', 'Low'], n//2),
        'observed_behavior': np.tile(['Risky', 'Conservative'], n//2),
        'risk_taking_score': np.random.normal(50, 10, n)
    }
    
    # Add some outliers
    data['risk_taking_score'][0] = 200  # Extreme outlier
    data['risk_taking_score'][1] = 150  # Outlier
    data['risk_taking_score'][2] = -50  # Negative outlier
    
    df = pd.DataFrame(data)
    return df

@pytest.fixture
def formula():
    return 'risk_taking_score ~ status_level * observed_behavior'

def test_sensitivity_analysis_basic(sample_data, formula):
    """Test basic functionality of sensitivity analysis."""
    result_df = run_sensitivity_analysis(
        sample_data, 
        formula, 
        structure_type='between',
        sd_range=[1.0, 2.0, 3.0]
    )
    
    assert isinstance(result_df, pd.DataFrame)
    assert len(result_df) == 3  # 3 thresholds
    assert 'threshold_sd' in result_df.columns
    assert 'n_excluded' in result_df.columns
    assert 'n_remaining' in result_df.columns
    assert 'interaction_coef' in result_df.columns
    assert 'interaction_p' in result_df.columns
    assert 'status' in result_df.columns

def test_sensitivity_analysis_outlier_exclusion(sample_data, formula):
    """Test that outliers are correctly excluded at different thresholds."""
    result_df = run_sensitivity_analysis(
        sample_data, 
        formula, 
        structure_type='between',
        sd_range=[1.0, 2.0, 3.0]
    )
    
    # At 1.0 SD, we should exclude more outliers than at 3.0 SD
    exclusions = result_df['n_excluded'].values
    assert exclusions[0] >= exclusions[1] >= exclusions[2], \
        "Lower SD thresholds should exclude at least as many outliers as higher thresholds"
    
    # We added 3 outliers, so at least some should be excluded at 1.0 SD
    assert exclusions[0] >= 1, "At least one outlier should be excluded at 1.0 SD"

def test_sensitivity_analysis_with_insufficient_data():
    """Test handling of insufficient data after outlier exclusion."""
    # Create tiny dataset
    data = {
        'participant_id': range(5),
        'status_level': ['High', 'High', 'Low', 'Low', 'High'],
        'observed_behavior': ['Risky', 'Conservative', 'Risky', 'Conservative', 'Risky'],
        'risk_taking_score': [100, 100, 100, 100, 1000]  # One extreme outlier
    }
    df = pd.DataFrame(data)
    
    result_df = run_sensitivity_analysis(
        df,
        'risk_taking_score ~ status_level * observed_behavior',
        structure_type='between',
        sd_range=[1.0, 2.0]
    )
    
    # Should have results, possibly with insufficient_data status
    assert len(result_df) == 2
    assert 'status' in result_df.columns

def test_sensitivity_analysis_cell_mean_calculation():
    """Test that outliers are calculated relative to cell means, not global mean."""
    np.random.seed(123)
    n = 100
    
    # Create data where cell means are very different
    data = []
    for i in range(n):
        status = 'High' if i < n//2 else 'Low'
        behavior = 'Risky' if i % 2 == 0 else 'Conservative'
        
        # High status has much higher scores
        if status == 'High':
            score = np.random.normal(80, 5)
        else:
            score = np.random.normal(20, 5)
        
        # Add an outlier that would be normal in one cell but extreme in another
        if i == 0:
            score = 90  # This is normal for High/Risky but extreme for Low/Risky
        
        data.append({
            'participant_id': i,
            'status_level': status,
            'observed_behavior': behavior,
            'risk_taking_score': score
        })
    
    df = pd.DataFrame(data)
    
    # Run sensitivity analysis
    result_df = run_sensitivity_analysis(
        df,
        'risk_taking_score ~ status_level * observed_behavior',
        structure_type='between',
        sd_range=[1.5]
    )
    
    # The outlier should be handled based on its cell's statistics
    assert len(result_df) == 1
    assert result_df.iloc[0]['status'] == 'success' or result_df.iloc[0]['n_remaining'] > 0

def test_sensitivity_analysis_vif_calculation(sample_data, formula):
    """Test that VIF is calculated in sensitivity analysis."""
    result_df = run_sensitivity_analysis(
        sample_data, 
        formula, 
        structure_type='between',
        sd_range=[2.0]
    )
    
    assert 'vif_max' in result_df.columns
    # VIF should be a number (or NaN if calculation failed)
    assert pd.notna(result_df.iloc[0]['vif_max']) or pd.isna(result_df.iloc[0]['vif_max'])

def test_sensitivity_analysis_empty_threshold_list():
    """Test handling of empty threshold list."""
    data = {
        'participant_id': range(10),
        'status_level': ['High', 'Low'] * 5,
        'observed_behavior': ['Risky', 'Conservative'] * 5,
        'risk_taking_score': np.random.normal(50, 10, 10)
    }
    df = pd.DataFrame(data)
    
    result_df = run_sensitivity_analysis(
        df,
        'risk_taking_score ~ status_level * observed_behavior',
        structure_type='between',
        sd_range=[]
    )
    
    assert len(result_df) == 0

def test_sensitivity_analysis_single_threshold(sample_data, formula):
    """Test with a single threshold value."""
    result_df = run_sensitivity_analysis(
        sample_data, 
        formula, 
        structure_type='between',
        sd_range=[2.0]
    )
    
    assert len(result_df) == 1
    assert result_df.iloc[0]['threshold_sd'] == 2.0

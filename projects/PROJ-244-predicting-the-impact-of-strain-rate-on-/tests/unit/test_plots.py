import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor

# Add code directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from visualization.plots import (
    get_representative_alloy_families,
    generate_partial_dependence_plots,
    load_config
)

@pytest.fixture
def sample_df():
    """Create a mock dataset with multiple alloy families."""
    np.random.seed(42)
    n = 300
    families = ['AA-6061', 'AISI-4340', 'Ti-6Al-4V', 'Al-7075']
    # Distribute unevenly to test 'largest N' logic
    counts = [150, 80, 50, 20]
    
    data = {
        'alloy_family': np.repeat(families, counts),
        'strain_rate_s_inv': np.random.uniform(-2, 2, n), # log scale approx
        'yield_strength_mpa': np.random.uniform(200, 800, n),
        'temperature_k': np.random.uniform(298, 600, n),
        'grain_size_um': np.random.uniform(1, 100, n),
    }
    # Add elemental fractions (simulated columns)
    for i in range(10):
        data[f'elem_{i}'] = np.random.rand(n)
        
    return pd.DataFrame(data)

@pytest.fixture
def mock_model():
    """Create a mock sklearn pipeline."""
    # Create a simple dummy regressor
    clf = RandomForestRegressor(n_estimators=5, random_state=42)
    # Mock the pipeline to avoid actual training requirements
    pipe = Pipeline([('regressor', clf)])
    # Mock feature_names_in_ to match our sample data
    pipe.feature_names_in_ = [
        'strain_rate_s_inv', 'temperature_k', 'grain_size_um', 
        'elem_0', 'elem_1', 'elem_2', 'elem_3', 'elem_4', 
        'elem_5', 'elem_6', 'elem_7', 'elem_8', 'elem_9'
    ]
    return pipe

def test_get_representative_alloy_families(sample_df):
    """Test that the function selects the top 3 families by count."""
    result = get_representative_alloy_families(sample_df, n_families=3)
    
    # Expected top 3: AA-6061 (150), AISI-4340 (80), Ti-6Al-4V (50)
    expected = ['AA-6061', 'AISI-4340', 'Ti-6Al-4V']
    
    assert result == expected
    assert len(result) == 3

def test_get_representative_alloy_families_fewer_than_n(sample_df):
    """Test behavior when fewer families exist than requested."""
    # Create a df with only 2 families
    small_df = sample_df[sample_df['alloy_family'].isin(['AA-6061', 'AISI-4340'])]
    
    result = get_representative_alloy_families(small_df, n_families=5)
    
    assert len(result) == 2
    assert 'AA-6061' in result
    assert 'AISI-4340' in result

def test_generate_partial_dependence_plots(mock_model, sample_df, tmp_path):
    """Test PDP generation for a single family."""
    # Mock the config to use tmp_path
    with patch('visualization.plots.load_config') as mock_cfg:
        mock_cfg.return_value = {
            'RESULTS_DIR': str(tmp_path),
            'MODELS_DIR': 'dummy',
            'DATA_PROCESSED': 'dummy'
        }
        
        # Filter to one family for simpler testing
        family_df = sample_df[sample_df['alloy_family'] == 'AA-6061'].copy()
        
        # Ensure enough samples
        if len(family_df) < 10:
            pytest.skip("Not enough samples for PDP")
        
        output_files = generate_partial_dependence_plots(
            mock_model,
            family_df,
            feature_name='strain_rate_s_inv',
            target_families=['AA-6061']
        )
        
        assert 'AA-6061' in output_files
        assert os.path.exists(output_files['AA-6061'])
        assert output_files['AA-6061'].endswith('.png')

def test_generate_partial_dependence_plots_missing_feature(mock_model, sample_df, tmp_path):
    """Test handling of missing feature name."""
    with patch('visualization.plots.load_config') as mock_cfg:
        mock_cfg.return_value = {
            'RESULTS_DIR': str(tmp_path),
            'MODELS_DIR': 'dummy',
            'DATA_PROCESSED': 'dummy'
        }
        
        # Remove the target feature
        df_no_feature = sample_df.drop(columns=['strain_rate_s_inv'])
        
        # Should raise ValueError or handle gracefully (depending on impl)
        # Based on implementation, it raises ValueError if not found
        with pytest.raises(ValueError):
            generate_partial_dependence_plots(
                mock_model,
                df_no_feature,
                feature_name='strain_rate_s_inv',
                target_families=['AA-6061']
            )

def test_config_loading():
    """Test that load_config returns expected structure."""
    config = load_config()
    assert 'DATA_PROCESSED' in config
    assert 'RANDOM_SEED' in config

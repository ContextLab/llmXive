import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import sys
import os

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.diagnostics import (
    calculate_vif, 
    drop_high_vif_predictors, 
    resolve_multicollinearity_and_retest
)

@pytest.fixture
def sample_data_with_high_vif():
    """
    Create a synthetic dataset where 'functional_role' is highly correlated with 'log_freq'
    to simulate high VIF.
    """
    n = 1000
    np.random.seed(42)
    
    # Create high correlation
    log_freq = np.random.normal(0, 1, n)
    # functional_role is almost identical to log_freq + noise
    functional_role = log_freq + np.random.normal(0, 0.1, n)
    similarity = np.random.normal(0, 1, n)
    target = (log_freq + similarity + np.random.normal(0, 0.1, n) > 0).astype(int)
    
    df = pd.DataFrame({
        'log_freq': log_freq,
        'functional_role': functional_role,
        'flavor_similarity': similarity,
        'compatibility_label': target
    })
    return df

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary directory for output files."""
    return tmp_path

def test_vif_calculation_high_correlation(sample_data_with_high_vif):
    """Test that VIF is high (> 5) for correlated features."""
    features = ['log_freq', 'functional_role', 'flavor_similarity']
    vif_df = calculate_vif(sample_data_with_high_vif, features)
    
    # Check that functional_role or log_freq has high VIF
    vif_values = vif_df['vif'].values
    assert any(v > 5 for v in vif_values), "Expected at least one VIF > 5 for correlated data"
    
    # Specifically check functional_role if it's in the list
    if 'functional_role' in vif_df['feature'].values:
        role_vif = vif_df[vif_df['feature'] == 'functional_role']['vif'].values[0]
        # It should be high due to correlation with log_freq
        assert role_vif > 5, f"Expected high VIF for functional_role, got {role_vif}"

def test_drop_high_vif_predictors(sample_data_with_high_vif):
    """Test that the function drops the high VIF predictor."""
    features = ['log_freq', 'functional_role', 'flavor_similarity']
    
    # We need to pass the full dataframe to the drop function
    # The function signature expects a dataframe and feature list?
    # Our implementation: drop_high_vif_predictors(df, threshold)
    # It internally identifies features.
    
    # Let's test the logic manually or via the full function
    # Since drop_high_vif_predictors in our code iterates on potential_features,
    # we can test it.
    
    reduced_df, dropped = drop_high_vif_predictors(sample_data_with_high_vif, threshold=5.0)
    
    # We expect 'functional_role' or 'log_freq' to be dropped
    assert len(dropped) > 0, "Expected at least one predictor to be dropped"
    assert 'functional_role' in dropped or 'log_freq' in dropped, \
        f"Expected functional_role or log_freq to be dropped, got {dropped}"
    
    # Check that the dropped column is not in the reduced_df
    for col in dropped:
        assert col not in reduced_df.columns, f"Column {col} should not be in reduced_df"

def test_resolve_multicollinearity_and_retest_creates_files(sample_data_with_high_vif, temp_output_dir):
    """Test that T043 main function creates the required JSON files."""
    # Save sample data to temp location
    data_path = temp_output_dir / "merged_dataset.csv"
    sample_data_with_high_vif.to_csv(data_path, index=False)
    
    lrt_path = temp_output_dir / "lrt_result_vif_corrected.json"
    comparison_path = temp_output_dir / "model_comparison.json"
    
    # Run the function
    result = resolve_multicollinearity_and_retest(
        data_path=str(data_path),
        output_lrt_path=str(lrt_path),
        output_model_comparison_path=str(comparison_path)
    )
    
    # Check files exist
    assert lrt_path.exists(), "LRT result file not created"
    assert comparison_path.exists(), "Model comparison file not created"
    
    # Check content
    with open(lrt_path, 'r') as f:
        lrt_data = json.load(f)
    
    assert 'dropped_predictors' in lrt_data, "LRT result missing dropped_predictors"
    assert 'p_value' in lrt_data, "LRT result missing p_value"
    
    with open(comparison_path, 'r') as f:
        comp_data = json.load(f)
        
    assert 'dropped_predictors' in comp_data, "Comparison file missing dropped_predictors"
    assert 'vif_corrected_lrt' in comp_data, "Comparison file missing vif_corrected_lrt"
    
    # Verify that functional_role was dropped in this specific synthetic case
    # (since we created high correlation)
    assert 'functional_role' in result['dropped'], "Expected functional_role to be dropped in high VIF scenario"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

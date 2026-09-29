"""
Unit tests for the synthetic data generator (T010).
Verifies ground truth parameter recovery and data structure.
"""
import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from data.download import generate_synthetic_dataset, SYNTHETIC_PARAMS

def test_synthetic_data_structure():
    """Test that the generated dataframe has the correct columns and shape."""
    df = generate_synthetic_dataset()
    
    required_cols = [
        'participant_id', 'pre_self_esteem', 'post_self_esteem', 
        'comparison_tendency', 'avatar_condition', 'data_source_type', 'pipeline_label'
    ]
    
    assert all(col in df.columns for col in required_cols), "Missing required columns"
    assert len(df) >= 100, f"Sample size {len(df)} is less than 100"
    assert df['data_source_type'].iloc[0] == 'synthetic', "Data source type label incorrect"
    assert df['pipeline_label'].iloc[0] == 'Pipeline Validation Only', "Pipeline label incorrect"

def test_synthetic_parameter_recovery():
    """
    Test that the synthetic data actually reflects the ground truth parameters.
    We fit a simple OLS model to the generated data and check if coefficients are close to truth.
    """
    # Ensure reproducibility
    np.random.seed(SYNTHETIC_PARAMS["seed"])
    df = generate_synthetic_dataset()
    
    # Prepare data for regression
    # Model: post ~ 1 + avatar + comparison + avatar:comparison
    # Note: We ignore pre_self_esteem for this specific parameter recovery test 
    # as the generation model didn't use it as a covariate for post (it was generated independently).
    
    import statsmodels.formula.api as smf
    
    # Create interaction term manually for clarity or let formula handle it
    # Using formula: post_self_esteem ~ avatar_condition * comparison_tendency
    model = smf.ols('post_self_esteem ~ avatar_condition * comparison_tendency', data=df).fit()
    
    params = model.params
    
    # Ground Truth
    # Intercept (when avatar=0, comparison=0) -> should be close to 0
    # avatar_condition coefficient (main effect) -> should be close to 0.1
    # comparison_tendency coefficient (main effect) -> should be close to 0.1
    # avatar_condition:comparison_tendency (interaction) -> should be close to 0.2
    
    # Allow for some noise (sigma=1.0) with N=150
    tolerance = 0.15 
    
    assert abs(params['Intercept'] - SYNTHETIC_PARAMS['intercept']) < tolerance, \
        f"Intercept {params['Intercept']} deviates too much from {SYNTHETIC_PARAMS['intercept']}"
    
    assert abs(params['C(avatar_condition)[T.1]'] - SYNTHETIC_PARAMS['main_effect_avatar']) < tolerance, \
        f"Avatar effect {params['C(avatar_condition)[T.1]']} deviates too much"
        
    assert abs(params['comparison_tendency'] - SYNTHETIC_PARAMS['main_effect_comparison']) < tolerance, \
        f"Comparison effect {params['comparison_tendency']} deviates too much"
        
    assert abs(params['C(avatar_condition)[T.1]:comparison_tendency'] - SYNTHETIC_PARAMS['interaction_beta']) < tolerance, \
        f"Interaction effect {params['C(avatar_condition)[T.1]:comparison_tendency']} deviates too much"

def test_seed_reproducibility():
    """Test that running the generator twice with the same seed produces identical results."""
    np.random.seed(SYNTHETIC_PARAMS["seed"])
    df1 = generate_synthetic_dataset()
    
    np.random.seed(SYNTHETIC_PARAMS["seed"])
    df2 = generate_synthetic_dataset()
    
    pd.testing.assert_frame_equal(df1, df2)
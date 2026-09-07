import pytest
import pandas as pd
import numpy as np
from analysis.matching import calculate_smd, estimate_propensity_scores

def test_calculate_smd():
    """Test Standardized Mean Difference calculation."""
    treatment = np.array([10, 12, 11, 13, 14])
    control = np.array([9, 10, 11, 10, 12])
    
    smd = calculate_smd(treatment, control)
    
    assert isinstance(smd, float)

def test_calculate_smd_perfect_match():
    """Test SMD when groups are identical."""
    group = np.array([10, 11, 12, 13, 14])
    
    smd = calculate_smd(group, group)
    
    assert abs(smd) < 0.001

def test_estimate_propensity_scores():
    """Test propensity score estimation."""
    data = pd.DataFrame({
        'treatment': [1, 0, 1, 0, 1, 0],
        'covariate1': [10, 12, 11, 13, 14, 15],
        'covariate2': [5, 6, 5, 7, 6, 8]
    })
    
    scores = estimate_propensity_scores(data, treatment_col='treatment', 
                                        covariates=['covariate1', 'covariate2'])
    
    assert len(scores) == len(data)
    assert all(0 <= s <= 1 for s in scores)
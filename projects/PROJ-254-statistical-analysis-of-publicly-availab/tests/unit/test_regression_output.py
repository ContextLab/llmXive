import pytest
import pandas as pd
import numpy as np
import json
from pathlib import Path
import statsmodels.api as sm

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from regression import fit_linear_regression, output_regression_results

def test_regression_output_structure(tmp_path):
    """
    Test that output_regression_results creates a valid JSON file with expected keys.
    """
    # Create dummy data
    data = {
        'year': [2010, 2011, 2012, 2013, 2014],
        'mean_off_diagonal_similarity': [0.45, 0.44, 0.43, 0.42, 0.41]
    }
    df = pd.DataFrame(data)
    
    model = sm.OLS(df['mean_off_diagonal_similarity'], sm.add_constant(df['year']))
    results = model.fit(cov_type='HC3')
    
    output_file = tmp_path / "test_results.json"
    output_regression_results(results, output_file)
    
    assert output_file.exists(), "Output JSON file was not created."
    
    with open(output_file, 'r') as f:
        data_out = json.load(f)
    
    # Check structure
    assert "coefficients" in data_out
    assert "slope" in data_out["coefficients"]
    assert "value" in data_out["coefficients"]["slope"]
    assert "ci_95_lower" in data_out["coefficients"]["slope"]
    assert "ci_95_upper" in data_out["coefficients"]["slope"]
    assert "p_value" in data_out["coefficients"]["slope"]
    
    assert "fit_statistics" in data_out
    assert "r_squared" in data_out["fit_statistics"]
    assert "n_obs" in data_out["fit_statistics"]

def test_regression_slope_sign(tmp_path):
    """
    Test that a decreasing trend results in a negative slope.
    """
    # Create dummy data with clear negative trend
    data = {
        'year': [2010, 2011, 2012, 2013, 2014],
        'mean_off_diagonal_similarity': [0.50, 0.45, 0.40, 0.35, 0.30]
    }
    df = pd.DataFrame(data)
    
    results = fit_linear_regression(df)
    
    assert results.params[1] < 0, "Slope should be negative for decreasing trend."
    assert results.params[1] < -0.01, "Slope magnitude should be significant."
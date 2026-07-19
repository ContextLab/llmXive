import pytest
import numpy as np
import pandas as pd
from scipy import stats
import sys
import os
from analysis.tests import run_scaled_t_test, run_scaled_anova, run_scaled_chi_squared

class TestPValueInvariance:
    def test_p_value_invariance(self):
        """Test p-value invariance under linear scaling."""
        # Generate data
        data = pd.DataFrame({"col1": np.random.rand(100), "col2": np.random.rand(100)})
        
        # Scale
        from preprocessing.scaling import standardize_data, min_max_scale
        scaled_std = standardize_data(data)
        scaled_minmax = min_max_scale(data)
        
        # Test
        result_std = run_scaled_t_test(scaled_std)
        result_minmax = run_scaled_t_test(scaled_minmax)
        
        # P-values should be similar
        assert np.isclose(result_std.p_value, result_minmax.p_value, atol=1e-10)

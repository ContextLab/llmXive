import os
import sys
import tempfile
import pandas as pd
import numpy as np
import pytest
from scipy import stats

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from evaluate import calculate_correlation_matrix, apply_bonferroni_correction

def test_calculate_correlation_matrix():
    """Test Pearson correlation calculation with known values."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create mock predictions
        pred_path = os.path.join(tmpdir, "predictions_GM12878.csv")
        pred_data = {
            'gene_id': ['G1', 'G2', 'G3', 'G4'],
            'predicted': [1.0, 2.0, 3.0, 4.0]
        }
        pd.DataFrame(pred_data).to_csv(pred_path, index=False)

        # Create mock actuals (perfect correlation)
        actual_path = os.path.join(tmpdir, "imputed_expression.csv")
        actual_data = {
            'gene_id': ['G1', 'G2', 'G3', 'G4'],
            'GM12878': [1.0, 2.0, 3.0, 4.0]
        }
        pd.DataFrame(actual_data).to_csv(actual_path, index=False)

        output_path = os.path.join(tmpdir, "corr.csv")
        
        # Run function
        result = calculate_correlation_matrix(pred_path, actual_path, output_path)
        
        assert os.path.exists(output_path)
        assert len(result) == 1
        assert result.iloc[0]['cell_line'] == 'GM12878'
        assert np.isclose(result.iloc[0]['pearson_correlation'], 1.0)
        assert np.isclose(result.iloc[0]['p_value'], 0.0)

def test_apply_bonferroni_correction():
    """Test Bonferroni correction logic."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "pvals.csv")
        data = {'p_value': [0.01, 0.05, 0.10]}
        pd.DataFrame(data).to_csv(input_path, index=False)
        
        output_path = os.path.join(tmpdir, "pvals_corrected.csv")
        
        result = apply_bonferroni_correction(input_path, output_path)
        
        assert os.path.exists(output_path)
        assert len(result) == 3
        # 0.01 * 3 = 0.03
        assert np.isclose(result.iloc[0]['p_value_corrected'], 0.03)
        # 0.10 * 3 = 0.30
        assert np.isclose(result.iloc[0]['p_value_corrected'], 0.03) # First row
        assert np.isclose(result.iloc[1]['p_value_corrected'], 0.15)
        assert np.isclose(result.iloc[2]['p_value_corrected'], 0.30)
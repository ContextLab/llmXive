import os
import sys
import pytest
import pandas as pd
import numpy as np
import pickle
import tempfile
import shutil

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from evaluate import (
    load_predictions, 
    load_actuals, 
    calculate_correlation_matrix, 
    apply_bonferroni_correction
)

class TestEvaluate:
    @pytest.fixture
    def temp_dir(self):
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp)

    def test_load_predictions_valid(self, temp_dir):
        data = pd.DataFrame({
            'gene_id': ['G1', 'G2'],
            'predicted_expression': [10.0, 20.0],
            'cell_line': ['GM12878', 'GM12878']
        })
        path = os.path.join(temp_dir, 'preds.pkl')
        with open(path, 'wb') as f:
            pickle.dump(data, f)
        
        result = load_predictions(path)
        assert len(result) == 2
        assert 'gene_id' in result.columns

    def test_load_actuals_valid(self, temp_dir):
        data = pd.DataFrame({
            'gene_id': ['G1', 'G2'],
            'expression': [10.5, 20.5],
            'cell_line': ['GM12878', 'GM12878']
        })
        path = os.path.join(temp_dir, 'actuals.csv')
        data.to_csv(path, index=False)
        
        result = load_actuals(path)
        assert len(result) == 2
        assert 'gene_id' in result.columns

    def test_calculate_correlation_matrix(self, temp_dir):
        # Create mock data where correlation is known
        # Perfect correlation
        preds = pd.DataFrame({
            'gene_id': ['G1', 'G2', 'G3'],
            'predicted_expression': [1.0, 2.0, 3.0],
            'cell_line': ['GM12878', 'GM12878', 'GM12878']
        })
        actuals = pd.DataFrame({
            'gene_id': ['G1', 'G2', 'G3'],
            'expression': [1.0, 2.0, 3.0],
            'cell_line': ['GM12878', 'GM12878', 'GM12878']
        })
        
        # Save to temp for load_predictions/actuals if needed, but functions take DataFrames
        # Direct test
        corr_df = calculate_correlation_matrix(preds, actuals)
        
        assert len(corr_df) == 1
        assert corr_df['correlation'].iloc[0] == pytest.approx(1.0)
        assert corr_df['p_value'].iloc[0] < 0.05 # Should be significant

    def test_apply_bonferroni_correction(self):
        df = pd.DataFrame({
            'cell_line': ['A', 'B', 'C'],
            'correlation': [0.9, 0.8, 0.7],
            'p_value': [0.01, 0.02, 0.03]
        })
        
        result = apply_bonferroni_correction(df, alpha=0.05)
        
        # n=3, so 0.01 * 3 = 0.03, 0.02 * 3 = 0.06, 0.03 * 3 = 0.09
        assert result['bonferroni_corrected_p'].iloc[0] == 0.03
        assert result['bonferroni_corrected_p'].iloc[1] == 0.06
        assert result['bonferroni_corrected_p'].iloc[2] == 0.09
        
        assert result['is_significant'].iloc[0] == True # 0.03 < 0.05
        assert result['is_significant'].iloc[1] == False # 0.06 > 0.05
        assert result['is_significant'].iloc[2] == False # 0.09 > 0.05

    def test_apply_bonferroni_correction_empty(self):
        df = pd.DataFrame(columns=['cell_line', 'correlation', 'p_value'])
        result = apply_bonferroni_correction(df)
        assert result.empty
        assert 'bonferroni_corrected_p' in result.columns

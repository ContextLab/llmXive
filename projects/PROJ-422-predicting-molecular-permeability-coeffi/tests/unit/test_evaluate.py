import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import json
import tempfile
import os
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.analysis.evaluate import calculate_metrics, paired_ttest, evaluate_models

class TestCalculateMetrics:
    def test_rmse_calculation(self):
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([1.1, 2.1, 2.9])
        metrics = calculate_metrics(y_true, y_pred)
        
        # Manual calculation:
        # errors: [0.1, 0.1, -0.1]
        # squared: [0.01, 0.01, 0.01] -> mean = 0.01 -> sqrt = 0.1
        assert abs(metrics['rmse'] - 0.1) < 1e-5
        assert metrics['mae'] == 0.1
        
    def test_r2_calculation(self):
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([1.0, 2.0, 3.0])
        metrics = calculate_metrics(y_true, y_pred)
        assert metrics['r2'] == 1.0
        
    def test_shape_mismatch(self):
        with pytest.raises(ValueError):
            calculate_metrics(np.array([1, 2]), np.array([1]))

class TestPairedTtest:
    def test_basic_ttest(self):
        # Identical arrays -> mean diff 0, p=1.0
        errors_a = np.array([1.0, 2.0, 3.0])
        errors_b = np.array([1.0, 2.0, 3.0])
        results = paired_ttest(errors_a, errors_b)
        
        assert results['mean_difference'] == 0.0
        assert abs(results['p_value'] - 1.0) < 1e-5
        assert results['cohens_d'] == 0.0
        
    def test_significant_difference(self):
        # Create a case where A is consistently worse than B
        errors_a = np.array([10.0, 11.0, 12.0, 13.0, 14.0])
        errors_b = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        results = paired_ttest(errors_a, errors_b)
        
        assert results['mean_difference'] > 0
        assert results['p_value'] < 0.05
        # Cohen's d should be large
        assert abs(results['cohens_d']) > 1.0
        
    def test_ci_bounds(self):
        errors_a = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        errors_b = np.array([1.5, 2.5, 3.5, 4.5, 5.5])
        results = paired_ttest(errors_a, errors_b)
        
        # Mean diff should be -0.5
        assert abs(results['mean_difference'] - (-0.5)) < 1e-5
        # CI should bracket the mean difference
        assert results['ci_lower'] <= results['mean_difference']
        assert results['ci_upper'] >= results['mean_difference']
        
    def test_insufficient_sample_size(self):
        with pytest.raises(ValueError):
            paired_ttest(np.array([1.0]), np.array([1.0]))

class TestEvaluateModelsIntegration:
    def test_full_evaluation_flow(self, tmp_path):
        # Create mock test data
        test_data = {
            'smiles': ['CCO', 'CCO', 'CCO'],
            'permeability_coefficient': [1.0, 2.0, 3.0]
        }
        test_df = pd.DataFrame(test_data)
        test_file = tmp_path / "test.csv"
        test_df.to_csv(test_file, index=False)
        
        # Mock predictions
        gnns_preds = np.array([1.1, 2.1, 2.9])
        rf_preds = np.array([1.5, 2.5, 3.5])
        
        output_file = tmp_path / "metrics.json"
        
        results = evaluate_models(test_file, gnns_preds, rf_preds, output_file)
        
        # Verify file creation
        assert output_file.exists()
        
        # Verify content structure
        with open(output_file) as f:
            data = json.load(f)
            
        assert 'gnn' in data
        assert 'random_forest_baseline' in data
        assert 'statistical_comparison' in data
        
        # Verify statistical keys
        stats = data['statistical_comparison']
        assert 't_statistic' in stats
        assert 'p_value' in stats
        assert 'cohens_d' in stats
        assert 'ci_lower' in stats
        assert 'ci_upper' in stats
        
        # Verify interpretation
        assert 'significant_at_0_05' in data['interpretation']
        assert 'effect_size_category' in data['interpretation']
import pytest
import numpy as np
import json
from pathlib import Path
import tempfile
import pandas as pd

from analysis.evaluate import calculate_metrics, paired_ttest, post_hoc_power_analysis, evaluate_models

class TestCalculateMetrics:
    def test_basic_metrics(self):
        y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = np.array([1.1, 2.1, 2.9, 4.2, 4.8])
        
        metrics = calculate_metrics(y_true, y_pred)
        
        assert "rmse" in metrics
        assert "mae" in metrics
        assert "r2" in metrics
        assert metrics["rmse"] > 0
        assert metrics["mae"] > 0
        assert metrics["r2"] <= 1.0
        
    def test_perfect_prediction(self):
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([1.0, 2.0, 3.0])
        
        metrics = calculate_metrics(y_true, y_pred)
        
        assert metrics["rmse"] == 0.0
        assert metrics["mae"] == 0.0
        assert metrics["r2"] == 1.0
        
    def test_mismatched_lengths(self):
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([1.0, 2.0])
        
        with pytest.raises(ValueError):
            calculate_metrics(y_true, y_pred)
            
    def test_empty_array(self):
        y_true = np.array([])
        y_pred = np.array([])
        
        with pytest.raises(ValueError):
            calculate_metrics(y_true, y_pred)

class TestPairedTtest:
    def test_basic_ttest(self):
        errors_a = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        errors_b = np.array([0.15, 0.25, 0.35, 0.45, 0.55])
        
        results = paired_ttest(errors_a, errors_b)
        
        assert "t_statistic" in results
        assert "p_value" in results
        assert "mean_diff" in results
        assert "std_diff" in results
        
    def test_identical_errors(self):
        errors_a = np.array([0.1, 0.2, 0.3])
        errors_b = np.array([0.1, 0.2, 0.3])
        
        results = paired_ttest(errors_a, errors_b)
        
        assert results["t_statistic"] == 0.0
        assert results["p_value"] == 1.0
        
    def test_mismatched_lengths(self):
        errors_a = np.array([0.1, 0.2, 0.3])
        errors_b = np.array([0.1, 0.2])
        
        with pytest.raises(ValueError):
            paired_ttest(errors_a, errors_b)

class TestPostHocPowerAnalysis:
    def test_basic_power(self):
        power_results = post_hoc_power_analysis(effect_size=0.8, n_samples=100)
        
        assert "power" in power_results
        assert "effect_size" in power_results
        assert "sample_size" in power_results
        assert 0 <= power_results["power"] <= 1.0
        
    def test_small_sample(self):
        power_results = post_hoc_power_analysis(effect_size=0.5, n_samples=1)
        
        assert power_results["power"] == 0.0
        assert "note" in power_results

class TestEvaluateModels:
    def test_evaluate_models_with_mock_data(self, tmp_path):
        # Create mock test data
        test_data = {
            "target": [1.0, 2.0, 3.0, 4.0, 5.0],
            "gnn_predictions": [1.1, 2.1, 2.9, 4.2, 4.8],
            "rf_baseline_predictions": [1.2, 1.9, 3.1, 3.8, 5.2]
        }
        test_df = pd.DataFrame(test_data)
        
        test_file = tmp_path / "test.csv"
        test_df.to_csv(test_file, index=False)
        
        # Create mock training log
        training_log = {
            "gnn": {"training_time": 100.0, "peak_memory_gb": 2.0},
            "rf_baseline": {"training_time": 50.0, "peak_memory_gb": 1.0}
        }
        training_log_file = tmp_path / "training_log.json"
        with open(training_log_file, 'w') as f:
            json.dump(training_log, f)
        
        # Run evaluation
        results = evaluate_models(project_root=tmp_path)
        
        assert "models" in results
        assert "gnn" in results["models"]
        assert "rf_baseline" in results["models"]
        assert "comparison" in results
        assert results["models"]["gnn"]["rmse"] > 0
        assert results["models"]["rf_baseline"]["rmse"] > 0
import pytest
import numpy as np
import os
import json
import tempfile
from pathlib import Path

# Import functions to test
from evaluation.metrics import compute_mae, compute_r2, compute_metrics_per_property, compute_all_statistics
from evaluation.evaluate import compute_evaluation_results

class TestEvaluationMetrics:
    def test_compute_mae(self):
        """Test MAE calculation"""
        y_true = np.array([1.0, 2.0, 3.0, 4.0])
        y_pred = np.array([1.1, 2.1, 2.9, 4.2])
        
        mae = compute_mae(y_true, y_pred)
        expected = np.mean(np.abs(y_true - y_pred))
        assert np.isclose(mae, expected)

    def test_compute_r2(self):
        """Test R2 calculation"""
        y_true = np.array([1.0, 2.0, 3.0, 4.0])
        y_pred = np.array([1.0, 2.0, 3.0, 4.0]) # Perfect prediction
        
        r2 = compute_r2(y_true, y_pred)
        assert np.isclose(r2, 1.0)

    def test_compute_metrics_per_property(self):
        """Test metrics calculation for multiple properties"""
        y_true = np.array([[1.0, 2.0], [2.0, 3.0], [3.0, 4.0]])
        y_pred = np.array([[1.1, 2.1], [2.1, 3.1], [3.1, 4.1]])
        
        metrics = compute_metrics_per_property(y_pred, y_true)
        
        assert "dipole" in metrics
        assert "polarizability" in metrics
        assert "mae" in metrics["dipole"]
        assert "r2" in metrics["dipole"]

    def test_compute_all_statistics(self):
        """Test statistical tests (t-test, TOST, Hotelling's)"""
        errors = np.array([[0.1, -0.1], [0.2, 0.0], [-0.1, 0.1]])
        
        stats = compute_all_statistics(errors)
        
        assert "paired_ttest" in stats
        assert "tost" in stats
        assert "hotellings_t2" in stats

    def test_compute_evaluation_results_saves_json(self):
        """Test that evaluate.py writes the JSON file correctly"""
        predictions = np.array([[1.1, 2.1, 3.1], [2.1, 3.1, 4.1]])
        targets = np.array([[1.0, 2.0, 3.0], [2.0, 3.0, 4.0]])
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_results.json")
            result = compute_evaluation_results(predictions, targets, output_path)
            
            assert os.path.exists(output_path)
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert "metrics" in data
            assert "statistical_tests" in data
            assert "sample_size" in data
            assert data["sample_size"] == 2

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

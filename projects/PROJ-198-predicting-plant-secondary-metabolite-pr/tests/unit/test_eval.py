import os
import sys
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import json

# Add the code directory to the path
code_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(code_dir))

from modeling.eval import (
    evaluate_models,
    calculate_significance,
    save_metrics,
    load_model_results,
    run_phylogenetic_permutation
)

class TestEvaluateModels:
    """Unit tests for evaluate_models function."""

    def test_evaluate_models_basic(self):
        """Test basic R² and Pearson correlation calculation."""
        y_true = [1.0, 2.0, 3.0, 4.0, 5.0]
        y_pred = [1.1, 2.1, 2.9, 4.1, 5.0]
        
        metrics = evaluate_models(y_true, y_pred, "test_model")
        
        assert "r2" in metrics
        assert "pearson_r" in metrics
        assert "pearson_p" in metrics
        assert "rmse" in metrics
        assert "mae" in metrics
        assert "model_name" in metrics
        assert metrics["model_name"] == "test_model"
        assert metrics["n_samples"] == 5
        
        # R² should be close to 1 for nearly perfect predictions
        assert metrics["r2"] > 0.9
        
        # Pearson r should be close to 1
        assert metrics["pearson_r"] > 0.9

    def test_evaluate_models_perfect_prediction(self):
        """Test with perfect predictions (R² = 1)."""
        y_true = [1.0, 2.0, 3.0, 4.0, 5.0]
        y_pred = [1.0, 2.0, 3.0, 4.0, 5.0]
        
        metrics = evaluate_models(y_true, y_pred, "perfect_model")
        
        assert abs(metrics["r2"] - 1.0) < 1e-10
        assert abs(metrics["pearson_r"] - 1.0) < 1e-10

    def test_evaluate_models_mismatched_lengths(self):
        """Test that mismatched lengths raise an error."""
        y_true = [1.0, 2.0, 3.0]
        y_pred = [1.0, 2.0]
        
        with pytest.raises(ValueError, match="must have the same length"):
            evaluate_models(y_true, y_pred)

    def test_evaluate_models_empty_input(self):
        """Test that empty input raises an error."""
        y_true = []
        y_pred = []
        
        with pytest.raises(ValueError, match="Input arrays are empty"):
            evaluate_models(y_true, y_pred)

    def test_evaluate_models_numpy_arrays(self):
        """Test with numpy arrays as input."""
        y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = np.array([1.1, 2.1, 2.9, 4.1, 5.0])
        
        metrics = evaluate_models(y_true, y_pred, "numpy_model")
        
        assert metrics["r2"] > 0.9
        assert metrics["pearson_r"] > 0.9

    def test_evaluate_models_pandas_series(self):
        """Test with pandas Series as input."""
        y_true = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = pd.Series([1.1, 2.1, 2.9, 4.1, 5.0])
        
        metrics = evaluate_models(y_true, y_pred, "pandas_model")
        
        assert metrics["r2"] > 0.9
        assert metrics["pearson_r"] > 0.9

class TestCalculateSignificance:
    """Unit tests for calculate_significance function."""

    def test_significant_result(self):
        """Test when observed R² is significantly better than baseline."""
        result = calculate_significance(
            observed_r2=0.5,
            baseline_r2=0.1,
            baseline_std=0.05,
            threshold=0.05
        )
        
        assert result["is_significant"] is True
        assert result["z_score"] > 0
        assert result["p_value"] < 0.05

    def test_non_significant_result(self):
        """Test when observed R² is not significantly better than baseline."""
        result = calculate_significance(
            observed_r2=0.15,
            baseline_r2=0.1,
            baseline_std=0.05,
            threshold=0.05
        )
        
        # With such a small difference, it's likely not significant
        assert result["z_score"] == 1.0  # (0.15 - 0.1) / 0.05
        # p-value will be around 0.16, which is > 0.05
        assert result["p_value"] > 0.05

    def test_zero_baseline_std(self):
        """Test when baseline standard deviation is zero."""
        result = calculate_significance(
            observed_r2=0.5,
            baseline_r2=0.1,
            baseline_std=0.0,
            threshold=0.05
        )
        
        assert result["is_significant"] is True
        assert result["z_score"] == float('inf')
        assert result["p_value"] == 0.0

    def test_observed_worse_than_baseline(self):
        """Test when observed R² is worse than baseline."""
        result = calculate_significance(
            observed_r2=0.05,
            baseline_r2=0.1,
            baseline_std=0.05,
            threshold=0.05
        )
        
        assert result["is_significant"] is False
        assert result["z_score"] < 0
        assert result["p_value"] > 0.5

class TestSaveMetrics:
    """Unit tests for save_metrics function."""

    def test_save_metrics_creates_file(self):
        """Test that save_metrics creates a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_metrics.json"
            metrics = {"r2": 0.5, "model": "test"}
            
            result_path = save_metrics(metrics, output_path)
            
            assert result_path.exists()
            assert result_path == output_path
            
            # Verify contents
            with open(result_path, 'r') as f:
                loaded = json.load(f)
            
            assert loaded["r2"] == 0.5
            assert loaded["model"] == "test"

    def test_save_metrics_default_path(self):
        """Test save_metrics with default path (should handle gracefully)."""
        metrics = {"r2": 0.5}
        
        # This might fail if default path doesn't exist, but shouldn't crash
        try:
            save_metrics(metrics)
        except (OSError, FileNotFoundError):
            # Expected if default path is not writable or doesn't exist
            pass

class TestLoadModelResults:
    """Unit tests for load_model_results function."""

    def test_load_model_results_valid_file(self):
        """Test loading from a valid JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results_path = Path(tmpdir) / "results.json"
            results_data = {"models": {"rf": {"r2": 0.5}}, "evaluations": {}}
            
            with open(results_path, 'w') as f:
                json.dump(results_data, f)
            
            loaded = load_model_results(results_path)
            
            assert loaded == results_data

    def test_load_model_results_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            load_model_results(Path("/nonexistent/path/results.json"))

    def test_load_model_results_invalid_json(self):
        """Test that JSONDecodeError is raised for invalid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results_path = Path(tmpdir) / "results.json"
            
            with open(results_path, 'w') as f:
                f.write("not valid json")
            
            with pytest.raises(json.JSONDecodeError):
                load_model_results(results_path)

class TestRunPhylogeneticPermutation:
    """Unit tests for run_phylogenetic_permutation function."""

    def test_permutation_runs(self):
        """Test that the permutation function runs without error."""
        y = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        X = np.random.randn(5, 2)
        
        result = run_phylogenetic_permutation(
            y=y,
            tree=None,  # Simplified test without actual tree
            n_permutations=10,
            X=X
        )
        
        assert "mean_baseline_r2" in result
        assert "std_baseline_r2" in result
        assert result["n_permutations"] == 10
        assert result["n_successful"] <= 10

    def test_permutation_with_default_model(self):
        """Test permutation with default model function."""
        y = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        
        result = run_phylogenetic_permutation(
            y=y,
            tree=None,
            n_permutations=5
        )
        
        assert "mean_baseline_r2" in result
        assert "std_baseline_r2" in result

    def test_permutation_zero_iterations(self):
        """Test with zero permutations."""
        y = np.array([1.0, 2.0, 3.0])
        
        result = run_phylogenetic_permutation(
            y=y,
            tree=None,
            n_permutations=0
        )
        
        assert result["mean_baseline_r2"] == 0.0
        assert result["n_successful"] == 0
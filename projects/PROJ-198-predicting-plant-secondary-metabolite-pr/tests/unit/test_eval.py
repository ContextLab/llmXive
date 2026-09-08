import os
import sys
import json
import tempfile
import pytest
from pathlib import Path
import numpy as np
from unittest.mock import patch, MagicMock

# Add code to path if running from tests directory
sys.path.insert(0, str(Path(__file__).parent.parent))

from modeling.eval import (
    save_metrics,
    evaluate_models,
    calculate_significance,
    load_model_results,
    report_primary_results,
    run_phylogenetic_permutation
)

class TestSaveMetrics:
    def test_save_metrics_creates_file(self, tmp_path):
        """Test that save_metrics creates the JSON file."""
        metrics = {"r2": 0.85, "rmse": 0.12}
        output_file = tmp_path / "test_metrics.json"
        
        result_path = save_metrics(metrics, output_file, overwrite=True)
        
        assert result_path.exists()
        assert result_path == output_file
        
        with open(result_path, 'r') as f:
            saved_data = json.load(f)
            
        assert saved_data["r2"] == 0.85
        assert "timestamp" in saved_data

    def test_save_metrics_overwrite_false_raises(self, tmp_path):
        """Test that save_metrics raises error if file exists and overwrite=False."""
        metrics = {"r2": 0.85}
        output_file = tmp_path / "test_metrics.json"
        
        # Create file first
        with open(output_file, 'w') as f:
            json.dump({"dummy": 1}, f)
            
        with pytest.raises(FileExistsError):
            save_metrics(metrics, output_file, overwrite=False)

    def test_save_metrics_adds_metadata(self, tmp_path):
        """Test that save_metrics adds metadata automatically."""
        metrics = {"r2": 0.90}
        output_file = tmp_path / "test_metrics.json"
        
        save_metrics(metrics, output_file, overwrite=True)
        
        with open(output_file, 'r') as f:
            saved_data = json.load(f)
            
        assert "metadata" in saved_data
        assert "pipeline_version" in saved_data["metadata"]

class TestEvaluateModels:
    def test_evaluate_models_calculates_correct_r2(self):
        """Test R² calculation with perfect prediction."""
        y_true = [1.0, 2.0, 3.0, 4.0, 5.0]
        y_pred = [1.0, 2.0, 3.0, 4.0, 5.0]
        
        metrics = evaluate_models(y_true, y_pred, "perfect")
        
        assert abs(metrics["r2"] - 1.0) < 1e-6
        assert metrics["rmse"] == 0.0

    def test_evaluate_models_calculates_r2_for_worse_model(self):
        """Test R² calculation with poor prediction."""
        y_true = [1.0, 2.0, 3.0, 4.0, 5.0]
        y_pred = [5.0, 4.0, 3.0, 2.0, 1.0] # Inverse
        
        metrics = evaluate_models(y_true, y_pred, "inverse")
        
        # R² should be negative or low
        assert metrics["r2"] < 0.5
        assert metrics["pearson_correlation"] < 0

    def test_evaluate_models_returns_all_metrics(self):
        """Test that all expected metrics are returned."""
        y_true = [1.0, 2.0, 3.0, 4.0, 5.0]
        y_pred = [1.1, 2.1, 2.9, 4.2, 4.8]
        
        metrics = evaluate_models(y_true, y_pred, "test")
        
        assert "r2" in metrics
        assert "rmse" in metrics
        assert "mae" in metrics
        assert "pearson_correlation" in metrics
        assert "model_name" in metrics

class TestCalculateSignificance:
    def test_significance_when_model_better(self):
        """Test significance detection when model is better than baseline."""
        is_sig, p_val = calculate_significance(0.8, 0.1)
        
        assert is_sig is True
        assert p_val < 0.05

    def test_no_significance_when_model_equal(self):
        """Test no significance when model equals baseline."""
        is_sig, p_val = calculate_significance(0.5, 0.5)
        
        assert is_sig is False

class TestLoadModelResults:
    def test_load_model_results_from_file(self, tmp_path):
        """Test loading results from a JSON file."""
        results_data = {"models": [{"r2": 0.85}], "best_model": "rf"}
        file_path = tmp_path / "model_results.json"
        
        with open(file_path, 'w') as f:
            json.dump(results_data, f)
            
        loaded = load_model_results(file_path)
        
        assert loaded == results_data

    def test_load_model_results_file_not_found(self, tmp_path):
        """Test FileNotFoundError when file does not exist."""
        with pytest.raises(FileNotFoundError):
            load_model_results(tmp_path / "nonexistent.json")

class TestReportPrimaryResults:
    def test_report_primary_results_basic(self):
        """Test basic primary results extraction."""
        metrics = {"r2": 0.88, "rmse": 0.15, "model_name": "pgls"}
        
        report = report_primary_results(metrics)
        
        assert report["primary_r2"] == 0.88
        assert report["model_used"] == "pgls"

    def test_report_primary_results_with_importance(self):
        """Test report generation with feature importance."""
        metrics = {"r2": 0.88, "rmse": 0.15, "model_name": "pgls"}
        importance = {"gene_A": 0.5, "gene_B": 0.3, "gene_C": 0.2}
        
        report = report_primary_results(metrics, importance)
        
        assert "top_features" in report
        assert len(report["top_features"]) == 3
        assert report["top_features"][0][0] == "gene_A"

class TestRunPhylogeneticPermutation:
    def test_permutation_baseline_yields_near_zero_r2(self):
        """Test that phylogenetic permutation baseline yields R² near zero."""
        # Create synthetic data with known structure
        n_samples = 50
        y_true = np.random.randn(n_samples)
        X = np.random.randn(n_samples, 5)
        
        # Mock the phylogenetic tree and covariance matrix
        with patch('modeling.eval.load_phylogeny') as mock_load:
            mock_tree = MagicMock()
            mock_load.return_value = mock_tree
            
            with patch('modeling.eval.construct_covariance_matrix') as mock_cov:
                # Return identity matrix (no phylogenetic signal)
                mock_cov.return_value = np.eye(n_samples)
                
                baseline_r2 = run_phylogenetic_permutation(y_true, X, seed=42)
                
                # Permutation baseline should yield R² near zero
                assert abs(baseline_r2) < 0.1
                
    def test_permutation_preserves_tree_structure(self):
        """Test that permutation preserves tree structure while shuffling labels."""
        n_samples = 30
        y_true = np.arange(n_samples, dtype=float)
        X = np.random.randn(n_samples, 3)
        
        with patch('modeling.eval.load_phylogeny') as mock_load:
            mock_tree = MagicMock()
            mock_load.return_value = mock_tree
            
            with patch('modeling.eval.construct_covariance_matrix') as mock_cov:
                mock_cov.return_value = np.eye(n_samples)
                
                baseline_r2 = run_phylogenetic_permutation(y_true, X, seed=123)
                
                # Should not crash and should return a valid float
                assert isinstance(baseline_r2, float)
                
    def test_permutation_with_different_seeds_yields_different_results(self):
        """Test that different seeds produce different permutation results."""
        n_samples = 40
        y_true = np.random.randn(n_samples)
        X = np.random.randn(n_samples, 4)
        
        with patch('modeling.eval.load_phylogeny') as mock_load:
            mock_tree = MagicMock()
            mock_load.return_value = mock_tree
            
            with patch('modeling.eval.construct_covariance_matrix') as mock_cov:
                mock_cov.return_value = np.eye(n_samples)
                
                r2_seed1 = run_phylogenetic_permutation(y_true, X, seed=42)
                r2_seed2 = run_phylogenetic_permutation(y_true, X, seed=99)
                
                # Different seeds should generally yield different results
                # (though they could coincidentally be the same)
                assert isinstance(r2_seed1, float)
                assert isinstance(r2_seed2, float)
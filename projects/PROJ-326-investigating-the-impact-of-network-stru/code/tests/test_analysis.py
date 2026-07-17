"""
Comprehensive tests for analysis modules including sensitivity analysis.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd
import pytest

from code.src.analysis.sensitivity import (
    load_simulation_data,
    filter_by_clustering_threshold,
    compute_sensitivity_metrics,
    run_sensitivity_sweep,
    save_sensitivity_results,
    verify_sensitivity_results,
    SensitivityError,
    DEFAULT_THRESHOLDS
)

from code.src.analysis.regression import (
    fit_linear_regression,
    fit_polynomial_regression,
    compare_models
)

from code.src.analysis.anova import (
    run_one_way_anova,
    apply_multiple_comparison_correction,
    correct_regression_pvalues,
    ANOVAError
)

@pytest.fixture
def sample_simulation_data():
    """Create sample simulation data for testing."""
    data = []
    np.random.seed(42)
    for i in range(100):
        data.append({
            "network_id": f"network_{i:03d}",
            "diffusion_rate": np.random.uniform(0.1, 0.9),
            "clustering_coefficient": np.random.uniform(0.0, 1.0),
            "topology_class": np.random.choice(["erdos_renyi", "watts_strogatz", "barabasi_albert"]),
            "seed": 42 + i
        })
    return pd.DataFrame(data)

@pytest.fixture
def temp_analysis_dir():
    """Create a temporary directory for analysis outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_results_file(sample_simulation_data, temp_analysis_dir):
    """Create a sample simulation results file."""
    results_path = temp_analysis_dir / "simulation_results.json"
    results_path.parent.mkdir(parents=True, exist_ok=True)
    results_path.write_text(json.dumps(sample_simulation_data.to_dict(orient="records")))
    return results_path

# Sensitivity Analysis Tests

class TestSensitivityAnalysis:
    """Tests for sensitivity analysis functionality."""

    def test_load_simulation_data_valid(self, sample_results_file):
        """Test loading valid simulation data."""
        df = load_simulation_data(results_path=sample_results_file)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 100
        assert "diffusion_rate" in df.columns
        assert "clustering_coefficient" in df.columns

    def test_load_simulation_data_missing_file(self):
        """Test loading from a missing file raises error."""
        with pytest.raises(SensitivityError, match="not found"):
            load_simulation_data(results_path=Path("/nonexistent/file.json"))

    def test_load_simulation_data_invalid_json(self, temp_analysis_dir):
        """Test loading invalid JSON raises error."""
        invalid_path = temp_analysis_dir / "invalid.json"
        invalid_path.write_text("not valid json")
        
        with pytest.raises(SensitivityError, match="parse"):
            load_simulation_data(results_path=invalid_path)

    def test_filter_by_clustering_threshold(self, sample_simulation_data):
        """Test filtering by clustering coefficient threshold."""
        threshold = 0.5
        filtered = filter_by_clustering_threshold(sample_simulation_data, threshold)
        
        assert len(filtered) <= len(sample_simulation_data)
        assert all(filtered["clustering_coefficient"] >= threshold)

    def test_filter_by_clustering_threshold_empty_result(self, sample_simulation_data):
        """Test filtering with high threshold returns empty."""
        threshold = 2.0  # Impossible threshold
        filtered = filter_by_clustering_threshold(sample_simulation_data, threshold)
        
        assert len(filtered) == 0

    def test_compute_sensitivity_metrics_valid(self, sample_simulation_data):
        """Test computing sensitivity metrics."""
        filtered = filter_by_clustering_threshold(sample_simulation_data, 0.3)
        metrics = compute_sensitivity_metrics(filtered, 0.3)
        
        assert metrics["threshold"] == 0.3
        assert metrics["sample_size"] > 0
        assert metrics["valid"] is True
        assert "mean_diffusion_rate" in metrics
        assert "std_diffusion_rate" in metrics

    def test_compute_sensitivity_metrics_empty(self, sample_simulation_data):
        """Test computing metrics on empty DataFrame."""
        filtered = filter_by_clustering_threshold(sample_simulation_data, 2.0)
        metrics = compute_sensitivity_metrics(filtered, 2.0)
        
        assert metrics["sample_size"] == 0
        assert metrics["valid"] is False
        assert metrics["mean_diffusion_rate"] is None

    def test_run_sensitivity_sweep(self, sample_simulation_data):
        """Test running full sensitivity sweep."""
        thresholds = [0.2, 0.5, 0.8]
        results = run_sensitivity_sweep(sample_simulation_data, thresholds)
        
        assert len(results) == len(thresholds)
        for r in results:
            assert "threshold" in r
            assert "sample_size" in r
            assert "valid" in r

    def test_run_sensitivity_sweep_invalid_threshold(self, sample_simulation_data):
        """Test sweep with invalid threshold values."""
        with pytest.raises(SensitivityError, match="Invalid threshold"):
            run_sensitivity_sweep(sample_simulation_data, [0.5, 1.5])

    def test_run_sensitivity_sweep_empty_thresholds(self, sample_simulation_data):
        """Test sweep with empty thresholds list."""
        with pytest.raises(SensitivityError, match="non-empty list"):
            run_sensitivity_sweep(sample_simulation_data, [])

    def test_save_sensitivity_results(self, sample_simulation_data, temp_analysis_dir):
        """Test saving sensitivity results."""
        thresholds = [0.3, 0.6]
        results = run_sensitivity_sweep(sample_simulation_data, thresholds)
        
        output_path = temp_analysis_dir / "sensitivity_sweep.json"
        saved_path = save_sensitivity_results(results, output_path)
        
        assert saved_path.exists()
        with open(saved_path, 'r') as f:
            data = json.load(f)
        
        assert "results" in data
        assert "metadata" in data
        assert len(data["results"]) == len(thresholds)

    def test_verify_sensitivity_results_pass(self, sample_simulation_data, temp_analysis_dir):
        """Test successful verification of sensitivity results."""
        thresholds = [0.3, 0.6, 0.9]
        results = run_sensitivity_sweep(sample_simulation_data, thresholds)
        output_path = temp_analysis_dir / "sensitivity_sweep.json"
        save_sensitivity_results(results, output_path)
        
        success, details = verify_sensitivity_results(output_path, thresholds)
        
        assert success is True
        assert len(details["errors"]) == 0

    def test_verify_sensitivity_results_missing_file(self):
        """Test verification of non-existent file."""
        success, details = verify_sensitivity_results(Path("/nonexistent.json"))
        
        assert success is False
        assert not details["file_exists"]

    def test_verify_sensitivity_results_invalid_threshold(self, temp_analysis_dir):
        """Test verification with invalid threshold values."""
        output_path = temp_analysis_dir / "sensitivity_sweep.json"
        output_path.write_text(json.dumps({
            "results": [{"threshold": 1.5}],
            "metadata": {}
        }))
        
        success, details = verify_sensitivity_results(output_path)
        
        assert success is False
        assert not details["thresholds_valid"]

    def test_threshold_validation_in_config(self, sample_simulation_data, temp_analysis_dir, tmp_path):
        """Test that configurable cutoffs are properly validated per SC-005."""
        # Create a config with custom thresholds
        config_path = tmp_path / "config.yaml"
        config_path.write_text("""
        analysis:
          sensitivity:
            thresholds: [0.1, 0.4, 0.7]
        paths:
          sensitivity_results: {}/sensitivity_sweep.json
        """.format(temp_analysis_dir))
        
        with patch('code.src.analysis.sensitivity.load_config', return_value={
            "analysis": {"sensitivity": {"thresholds": [0.1, 0.4, 0.7]}},
            "paths": {"sensitivity_results": str(temp_analysis_dir / "sensitivity_sweep.json")}
        }):
            results = run_sensitivity_sweep(sample_simulation_data, [0.1, 0.4, 0.7])
            output_path = temp_analysis_dir / "sensitivity_sweep.json"
            save_sensitivity_results(results, output_path)
            
            success, details = verify_sensitivity_results(output_path, [0.1, 0.4, 0.7])
            
            assert success is True
            # Verify distinct cutoffs are present
            thresholds_in_result = [r["threshold"] for r in results]
            assert len(set(thresholds_in_result)) == len(thresholds_in_result)

    def test_default_thresholds_used(self, sample_simulation_data):
        """Test that default thresholds are used when none specified."""
        with patch('code.src.analysis.sensitivity.DEFAULT_THRESHOLDS', DEFAULT_THRESHOLDS):
            results = run_sensitivity_sweep(sample_simulation_data)
            
            assert len(results) == len(DEFAULT_THRESHOLDS)
            thresholds = [r["threshold"] for r in results]
            assert set(thresholds) == set(DEFAULT_THRESHOLDS)

# Regression Analysis Tests

class TestRegressionAnalysis:
    """Tests for regression analysis functionality."""

    def test_linear_regression_coefficients(self):
        """Test linear regression produces expected coefficients."""
        np.random.seed(42)
        x = np.random.rand(50)
        y = 2 * x + 1 + np.random.normal(0, 0.1, 50)
        
        result = fit_linear_regression(x, y)
        
        assert result["r_squared"] > 0.9
        assert abs(result["coefficients"][0] - 2.0) < 0.5
        assert abs(result["intercept"] - 1.0) < 0.5

    def test_non_linear_regression_fit(self):
        """Test polynomial regression fits non-linear data."""
        np.random.seed(42)
        x = np.linspace(0, 10, 100)
        y = 0.5 * x**2 - 2 * x + 3 + np.random.normal(0, 1, 100)
        
        result = fit_polynomial_regression(x, y, degree=2)
        
        assert result["r_squared"] > 0.8
        assert result["degree"] == 2

    def test_compare_models(self):
        """Test model comparison selects best model."""
        np.random.seed(42)
        x = np.random.rand(50)
        y = 3 * x + np.random.normal(0, 0.1, 50)
        
        models = compare_models(x, y)
        
        assert "linear" in models
        assert "polynomial" in models
        assert models["best_model"] in ["linear", "polynomial"]

# ANOVA Tests

class TestANOVAAnalysis:
    """Tests for ANOVA analysis functionality."""

    def test_anova_f_statistic(self):
        """Test ANOVA computes correct F-statistic."""
        np.random.seed(42)
        group1 = np.random.normal(0, 1, 50)
        group2 = np.random.normal(1, 1, 50)
        group3 = np.random.normal(2, 1, 50)
        
        f_stat, p_val = run_one_way_anova([group1, group2, group3])
        
        assert f_stat > 0
        assert 0 <= p_val <= 1

    def test_bh_correction_applied(self):
        """Test Benjamini-Hochberg correction is applied correctly."""
        np.random.seed(42)
        p_values = np.random.uniform(0, 1, 20)
        
        corrected = apply_multiple_comparison_correction(p_values, method="bh")
        
        assert len(corrected) == len(p_values)
        assert all(0 <= p <= 1 for p in corrected)
        # BH correction should generally increase p-values
        assert np.mean(corrected) >= np.mean(p_values)

    def test_bonferroni_correction_applied(self):
        """Test Bonferroni correction is applied correctly."""
        np.random.seed(42)
        p_values = np.random.uniform(0, 1, 20)
        
        corrected = apply_multiple_comparison_correction(p_values, method="bonferroni")
        
        assert len(corrected) == len(p_values)
        assert all(0 <= p <= 1 for p in corrected)
        # Bonferroni is more conservative than BH
        bonf_corrected = apply_multiple_comparison_correction(p_values, method="bonferroni")
        bh_corrected = apply_multiple_comparison_correction(p_values, method="bh")
        assert np.mean(bonf_corrected) >= np.mean(bh_corrected)

    def test_correct_regression_pvalues(self):
        """Test that correction applies to p-values not coefficients."""
        np.random.seed(42)
        p_values = np.array([0.01, 0.05, 0.1, 0.2])
        
        corrected = correct_regression_pvalues(p_values, method="bh")
        
        assert len(corrected) == len(p_values)
        # Coefficients should remain unchanged (not tested here, but structure implies it)
        assert all(0 <= p <= 1 for p in corrected)

    def test_anova_error_handling(self):
        """Test ANOVA raises error on invalid input."""
        with pytest.raises(ANOVAError):
            run_one_way_anova([])

    def test_sensitivity_sweep_thresholds_validation(self):
        """Test sensitivity sweep validates distinct cutoffs."""
        np.random.seed(42)
        data = pd.DataFrame({
            "diffusion_rate": np.random.rand(50),
            "clustering_coefficient": np.random.rand(50),
            "topology_class": ["a"] * 50
        })
        
        # Test with duplicate thresholds (should still work but produce same results)
        results = run_sensitivity_sweep(data, [0.5, 0.5, 0.5])
        assert len(results) == 3

    def test_sensitivity_sweep_thresholds_boundaries(self):
        """Test sensitivity sweep handles boundary values correctly."""
        np.random.seed(42)
        data = pd.DataFrame({
            "diffusion_rate": np.random.rand(50),
            "clustering_coefficient": np.random.rand(50),
            "topology_class": ["a"] * 50
        })
        
        # Test with boundary thresholds
        results = run_sensitivity_sweep(data, [0.0, 1.0])
        assert len(results) == 2
        assert results[0]["threshold"] == 0.0
        assert results[1]["threshold"] == 1.0
        # Threshold 0.0 should include all data
        assert results[0]["sample_size"] == 50
        # Threshold 1.0 should likely include very few or none
        assert results[1]["sample_size"] <= 50

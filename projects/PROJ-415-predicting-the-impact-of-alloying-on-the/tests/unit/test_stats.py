"""
Unit tests for statistical validation module (T027, T029).
"""
import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
import json
import os
import tempfile
from pathlib import Path

# Import the module to test
from code.validation.stats import (
    compute_bootstrap_ci,
    load_linear_model_coefficients,
    run_validation_stats
)

class TestBootstrapCI:
    """Test the bootstrap confidence interval calculation."""

    def test_bootstrap_ci_basic(self):
        """Test basic bootstrap CI calculation with known linear relationship."""
        # Create synthetic data: y = 2 + 3*x + noise
        np.random.seed(42)
        n = 100
        X = np.random.rand(n)
        y = 2 + 3 * X + np.random.normal(0, 0.1, n)
        
        # Compute CI for the slope (index 1)
        lower, upper, point_est = compute_bootstrap_ci(
            X, y, 
            coefficient_index=1, 
            n_iterations=100, # Small for speed in tests
            confidence_level=0.95,
            random_seed=42
        )
        
        # Point estimate should be close to 3.0
        assert 2.5 < point_est < 3.5, f"Point estimate {point_est} is not close to expected 3.0"
        
        # Lower should be less than upper
        assert lower < upper, "Lower bound must be less than upper bound"
        
        # The true value (3.0) should ideally be within the CI (not guaranteed but likely)
        # We just check the bounds are reasonable
        assert lower < 3.5, "Lower bound seems too high"
        assert upper > 2.5, "Upper bound seems too low"

    def test_bootstrap_ci_intercept(self):
        """Test bootstrap CI for intercept (index 0)."""
        np.random.seed(42)
        n = 100
        X = np.random.rand(n)
        y = 5 + 1 * X + np.random.normal(0, 0.1, n)
        
        lower, upper, point_est = compute_bootstrap_ci(
            X, y, 
            coefficient_index=0, # Intercept
            n_iterations=100,
            confidence_level=0.95,
            random_seed=42
        )
        
        assert 4.5 < point_est < 5.5, f"Intercept estimate {point_est} is not close to expected 5.0"
        assert lower < upper

    def test_bootstrap_ci_with_small_sample(self):
        """Test bootstrap with small sample size."""
        np.random.seed(42)
        n = 20
        X = np.random.rand(n)
        y = 1 + 2 * X + np.random.normal(0, 0.1, n)
        
        lower, upper, point_est = compute_bootstrap_ci(
            X, y, 
            coefficient_index=1, 
            n_iterations=50, # Very small for speed
            confidence_level=0.95,
            random_seed=42
        )
        
        assert lower < upper

class TestLoadLinearModelCoefficients:
    """Test loading linear model coefficients."""

    def test_load_coefficients_success(self):
        """Test successful loading of coefficients."""
        with tempfile.TemporaryDirectory() as tmpdir:
            models_dir = Path(tmpdir) / "models"
            models_dir.mkdir()
            
            coef_path = models_dir / "linear_coef.json"
            test_data = {
                "coefficients": {"intercept": 1.0, "size_mismatch": 2.0},
                "p_values": {"size_mismatch": 0.01}
            }
            
            with open(coef_path, 'w') as f:
                json.dump(test_data, f)
            
            with patch('code.validation.stats.MODELS_DIR', str(models_dir)):
                result = load_linear_model_coefficients()
                
                assert result["coefficients"]["size_mismatch"] == 2.0
                assert result["p_values"]["size_mismatch"] == 0.01

    def test_load_coefficients_file_not_found(self):
        """Test error when coefficients file is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            models_dir = Path(tmpdir) / "models"
            models_dir.mkdir()
            
            with patch('code.validation.stats.MODELS_DIR', str(models_dir)):
                with pytest.raises(FileNotFoundError):
                    load_linear_model_coefficients()

class TestRunValidationStats:
    """Test the main validation function."""

    def test_run_validation_stats_success(self):
        """Test successful execution of validation stats."""
        # Create mock data
        mock_coef_data = {
            "coefficients": {"intercept": 1.0, "size_mismatch": 2.5},
            "p_values": {"size_mismatch": 0.03}
        }
        
        mock_df = pd.DataFrame({
            "size_mismatch": [0.1, 0.2, 0.3, 0.4, 0.5],
            "activation_energy": [1.0, 1.2, 1.4, 1.6, 1.8]
        })
        
        with tempfile.TemporaryDirectory() as tmpdir:
            models_dir = Path(tmpdir) / "models"
            data_dir = Path(tmpdir) / "data" / "curated"
            models_dir.mkdir()
            data_dir.mkdir(parents=True)
            
            # Write mock files
            with open(models_dir / "linear_coef.json", 'w') as f:
                json.dump(mock_coef_data, f)
            
            mock_df.to_csv(data_dir / "filtered.csv", index=False)
            
            # Patch paths
            with patch('code.validation.stats.MODELS_DIR', str(models_dir)):
                with patch('code.validation.stats.DATA_DIR', str(Path(tmpdir) / "data")):
                    with patch('code.validation.stats.REPORTS_DIR', str(Path(tmpdir) / "reports")):
                        # Mock the bootstrap function to return known values to avoid long runtime
                        with patch('code.validation.stats.compute_bootstrap_ci', return_value=(2.0, 3.0, 2.5)):
                            results = run_validation_stats()
                            
                            assert "coefficient_name" in results
                            assert results["p_value"] == 0.03
                            assert results["is_significant_at_0.05"] == True
                            assert results["bootstrap_ci_95"]["lower"] == 2.0
                            assert results["bootstrap_ci_95"]["upper"] == 3.0

    def test_run_validation_stats_not_significant(self):
        """Test when p-value is not significant."""
        mock_coef_data = {
            "coefficients": {"intercept": 1.0, "size_mismatch": 0.5},
            "p_values": {"size_mismatch": 0.15}
        }
        
        mock_df = pd.DataFrame({
            "size_mismatch": [0.1, 0.2, 0.3],
            "activation_energy": [1.0, 1.1, 1.2]
        })
        
        with tempfile.TemporaryDirectory() as tmpdir:
            models_dir = Path(tmpdir) / "models"
            data_dir = Path(tmpdir) / "data" / "curated"
            models_dir.mkdir()
            data_dir.mkdir(parents=True)
            
            with open(models_dir / "linear_coef.json", 'w') as f:
                json.dump(mock_coef_data, f)
            
            mock_df.to_csv(data_dir / "filtered.csv", index=False)
            
            with patch('code.validation.stats.MODELS_DIR', str(models_dir)):
                with patch('code.validation.stats.DATA_DIR', str(Path(tmpdir) / "data")):
                    with patch('code.validation.stats.REPORTS_DIR', str(Path(tmpdir) / "reports")):
                        with patch('code.validation.stats.compute_bootstrap_ci', return_value=(0.0, 1.0, 0.5)):
                            results = run_validation_stats()
                            
                            assert results["is_significant_at_0.05"] == False

    def test_run_validation_stats_missing_columns(self):
        """Test error when required columns are missing."""
        mock_df = pd.DataFrame({
            "wrong_column": [0.1, 0.2],
            "activation_energy": [1.0, 1.1]
        })
        
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir) / "data" / "curated"
            data_dir.mkdir(parents=True)
            
            mock_df.to_csv(data_dir / "filtered.csv", index=False)
            
            with patch('code.validation.stats.DATA_DIR', str(Path(tmpdir) / "data")):
                with pytest.raises(ValueError, match="Required columns"):
                    run_validation_stats()
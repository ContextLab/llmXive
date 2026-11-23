"""
Unit tests for the synthetic data generator module.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import json
import sys
import tempfile
import shutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from synthetic_generator import (
    generate_normal_distribution,
    generate_lognormal_distribution,
    generate_exponential_distribution,
    generate_beta_distribution,
    generate_gamma_distribution,
    save_ground_truth_params,
    generate_and_save_distribution
)

class TestSyntheticGenerator:
    """Test cases for synthetic data generation functions."""

    def test_normal_distribution_mean_variance(self):
        """Test that generated Normal distribution has correct mean and variance."""
        n_samples = 100000
        true_mean = 50.0
        true_std = 10.0
        
        data, params = generate_normal_distribution(n_samples, true_mean, true_std, seed=42)
        
        # Check parameters
        assert params["distribution"] == "Normal"
        assert params["true_mean"] == true_mean
        assert params["true_std"] == true_std
        assert abs(params["true_variance"] - true_std**2) < 1e-9
        
        # Check sample statistics (with tolerance for randomness)
        sample_mean = np.mean(data)
        sample_std = np.std(data)
        
        assert abs(sample_mean - true_mean) < 0.5  # Within 0.5 of true mean
        assert abs(sample_std - true_std) < 0.5    # Within 0.5 of true std

    def test_lognormal_distribution_variance(self):
        """Test that generated LogNormal distribution has correct variance."""
        n_samples = 100000
        mu = 0.0
        sigma = 0.5
        
        data, params = generate_lognormal_distribution(n_samples, mu, sigma, seed=42)
        
        # Calculate theoretical variance
        theoretical_variance = (np.exp(sigma**2) - 1) * np.exp(2*mu + sigma**2)
        
        # Check parameters
        assert params["distribution"] == "LogNormal"
        assert abs(params["true_variance"] - theoretical_variance) < 1e-9
        
        # Check sample variance (with tolerance)
        sample_variance = np.var(data)
        assert abs(sample_variance - theoretical_variance) / theoretical_variance < 0.05  # Within 5%

    def test_exponential_distribution_variance(self):
        """Test that generated Exponential distribution has correct variance."""
        n_samples = 100000
        scale = 2.0
        
        data, params = generate_exponential_distribution(n_samples, scale, seed=42)
        
        # Exponential variance = scale^2
        theoretical_variance = scale ** 2
        
        # Check parameters
        assert params["distribution"] == "Exponential"
        assert abs(params["true_variance"] - theoretical_variance) < 1e-9
        
        # Check sample variance (with tolerance)
        sample_variance = np.var(data)
        assert abs(sample_variance - theoretical_variance) / theoretical_variance < 0.05

    def test_beta_distribution_variance(self):
        """Test that generated Beta distribution has correct variance."""
        n_samples = 100000
        alpha = 2.0
        beta_param = 5.0
        
        data, params = generate_beta_distribution(n_samples, alpha, beta_param, seed=42)
        
        # Beta variance formula
        theoretical_variance = (alpha * beta_param) / ((alpha + beta_param)**2 * (alpha + beta_param + 1))
        
        # Check parameters
        assert params["distribution"] == "Beta"
        assert abs(params["true_variance"] - theoretical_variance) < 1e-9
        
        # Check sample variance (with tolerance)
        sample_variance = np.var(data)
        assert abs(sample_variance - theoretical_variance) / theoretical_variance < 0.05

    def test_gamma_distribution_variance(self):
        """Test that generated Gamma distribution has correct variance."""
        n_samples = 100000
        shape = 3.0
        scale = 2.0
        
        data, params = generate_gamma_distribution(n_samples, shape, scale, seed=42)
        
        # Gamma variance = shape * scale^2
        theoretical_variance = shape * (scale ** 2)
        
        # Check parameters
        assert params["distribution"] == "Gamma"
        assert abs(params["true_variance"] - theoretical_variance) < 1e-9
        
        # Check sample variance (with tolerance)
        sample_variance = np.var(data)
        assert abs(sample_variance - theoretical_variance) / theoretical_variance < 0.05

    def test_save_ground_truth_params(self):
        """Test saving ground truth parameters to JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_params.json"
            
            params_list = [
                {"distribution": "Normal", "true_variance": 100.0},
                {"distribution": "Exponential", "true_variance": 4.0}
            ]
            
            save_ground_truth_params(params_list, output_path)
            
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                loaded_params = json.load(f)
            
            assert len(loaded_params) == 2
            assert loaded_params[0]["distribution"] == "Normal"
            assert loaded_params[1]["distribution"] == "Exponential"

    def test_generate_and_save_distribution(self):
        """Test full pipeline of generating and saving a distribution."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "test_data.csv"
            
            params = generate_and_save_distribution(
                generator_func=generate_normal_distribution,
                n_samples=1000,
                output_csv_path=csv_path,
                param_args={"mean": 0.0, "std": 1.0},
                seed=42
            )
            
            # Check file exists
            assert csv_path.exists()
            
            # Check CSV content
            df = pd.read_csv(csv_path)
            assert "value" in df.columns
            assert "distribution" in df.columns
            assert len(df) == 1000
            assert df["distribution"].iloc[0] == "Normal"
            
            # Check returned params
            assert params["distribution"] == "Normal"
            assert params["true_variance"] == 1.0
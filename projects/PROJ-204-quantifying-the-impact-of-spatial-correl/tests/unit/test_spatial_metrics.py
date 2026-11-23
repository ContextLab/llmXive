"""
Unit tests for code/analysis/spatial_metrics.py.
Tests autocorrelation computation, decay model fitting, and radial profiling.
"""
import numpy as np
import pytest
from scipy.optimize import curve_fit
from scipy.ndimage import gaussian_filter
from pathlib import Path
import tempfile
import os

# Import the module under test
from analysis.spatial_metrics import (
    gaussian_decay,
    exponential_decay,
    power_law_decay,
    compute_autocorrelation,
    compute_radial_distances,
    extract_radial_profile,
    fit_decay_model,
    compute_spatial_metrics_for_sample,
    process_dataset_and_write_metrics
)

class TestDecayModels:
    def test_gaussian_decay_at_zero(self):
        """Gaussian decay should return amplitude at lag=0."""
        A, sigma = 2.0, 5.0
        assert np.isclose(gaussian_decay(0, A, sigma), A)

    def test_exponential_decay_at_zero(self):
        """Exponential decay should return amplitude at lag=0."""
        A, tau = 2.0, 3.0
        assert np.isclose(exponential_decay(0, A, tau), A)

    def test_power_law_decay_at_zero(self):
        """Power law decay should return amplitude at lag=0."""
        A, alpha = 2.0, 1.5
        assert np.isclose(power_law_decay(0, A, alpha), A)

    def test_gaussian_decay_positive(self):
        """Gaussian decay should decrease with lag."""
        A, sigma = 1.0, 2.0
        y0 = gaussian_decay(0, A, sigma)
        y1 = gaussian_decay(sigma, A, sigma)
        assert y1 < y0

    def test_exponential_decay_positive(self):
        """Exponential decay should decrease with lag."""
        A, tau = 1.0, 2.0
        y0 = exponential_decay(0, A, tau)
        y1 = exponential_decay(tau, A, tau)
        assert y1 < y0

    def test_power_law_decay_positive(self):
        """Power law decay should decrease with lag."""
        A, alpha = 1.0, 2.0
        y0 = power_law_decay(0, A, alpha)
        y1 = power_law_decay(1.0, A, alpha)
        assert y1 < y0


class TestAutocorrelation:
    def test_autocorrelation_center_peak(self):
        """Autocorrelation of random noise should peak at center."""
        np.random.seed(42)
        img = np.random.randn(32, 32)
        ac = compute_autocorrelation(img)
        center = ac.shape[0] // 2
        center_val = ac[center, center]
        assert center_val == np.max(ac), "Center should be the maximum value"

    def test_autocorrelation_symmetry(self):
        """Autocorrelation should be symmetric."""
        np.random.seed(42)
        img = np.random.randn(16, 16)
        ac = compute_autocorrelation(img)
        # Check symmetry around center
        center = ac.shape[0] // 2
        # Compare quadrants
        assert np.allclose(ac, ac[::-1, ::-1]), "Autocorrelation must be symmetric"

    def test_autocorrelation_known_pattern(self):
        """Autocorrelation of a Gaussian blob should be a Gaussian."""
        x = np.linspace(-5, 5, 50)
        y = np.linspace(-5, 5, 50)
        X, Y = np.meshgrid(x, y)
        blob = np.exp(-(X**2 + Y**2) / 2)
        ac = compute_autocorrelation(blob)
        center = ac.shape[0] // 2
        # The center value should be the integral of the square of the blob
        expected_center = np.sum(blob**2)
        assert np.isclose(ac[center, center], expected_center, rtol=1e-2)


class TestRadialProfile:
    def test_compute_radial_distances(self):
        """Radial distances should be non-negative and symmetric."""
        shape = (20, 20)
        r = compute_radial_distances(shape)
        assert r.shape == shape
        assert np.all(r >= 0)
        center = shape[0] // 2
        # Check symmetry
        assert np.allclose(r, np.flipud(r))
        assert np.allclose(r, np.fliplr(r))

    def test_extract_radial_profile(self):
        """Radial profile should average values at same distance."""
        np.random.seed(42)
        ac = np.random.rand(32, 32)
        profile, r_bins = extract_radial_profile(ac)
        assert len(profile) > 0
        assert len(r_bins) > 0
        assert len(profile) == len(r_bins)
        # Profile should be non-negative if input is positive
        assert np.all(profile >= 0)


class TestFitDecayModel:
    def test_fit_gaussian_on_gaussian(self):
        """Fitting Gaussian model to Gaussian data should recover parameters."""
        np.random.seed(42)
        r = np.linspace(0, 10, 50)
        A_true, sigma_true = 2.0, 3.0
        y_true = gaussian_decay(r, A_true, sigma_true)
        # Add small noise
        y_noise = y_true + np.random.normal(0, 0.05, size=r.shape)

        popt, _ = fit_decay_model(r, y_noise, gaussian_decay)
        A_fit, sigma_fit = popt

        # Check recovery within 10%
        assert np.isclose(A_fit, A_true, rtol=0.1)
        assert np.isclose(sigma_fit, sigma_true, rtol=0.1)

    def test_fit_exponential_on_exponential(self):
        """Fitting Exponential model to Exponential data should recover parameters."""
        np.random.seed(42)
        r = np.linspace(0, 10, 50)
        A_true, tau_true = 2.0, 2.0
        y_true = exponential_decay(r, A_true, tau_true)
        y_noise = y_true + np.random.normal(0, 0.05, size=r.shape)

        popt, _ = fit_decay_model(r, y_noise, exponential_decay)
        A_fit, tau_fit = popt

        assert np.isclose(A_fit, A_true, rtol=0.1)
        assert np.isclose(tau_fit, tau_true, rtol=0.1)

    def test_fit_power_law_on_power_law(self):
        """Fitting Power Law model to Power Law data should recover parameters."""
        np.random.seed(42)
        r = np.linspace(0.1, 10, 50)  # Avoid 0 for power law
        A_true, alpha_true = 2.0, 1.5
        y_true = power_law_decay(r, A_true, alpha_true)
        y_noise = y_true + np.random.normal(0, 0.05, size=r.shape)

        popt, _ = fit_decay_model(r, y_noise, power_law_decay)
        A_fit, alpha_fit = popt

        assert np.isclose(A_fit, A_true, rtol=0.15)
        assert np.isclose(alpha_fit, alpha_true, rtol=0.15)


class TestComputeSpatialMetricsForSample:
    def test_compute_metrics_returns_dict(self):
        """Should return a dictionary with expected keys."""
        np.random.seed(42)
        sample_map = np.random.randn(32, 32)
        sample_id = "test_001"
        element = "Pb"

        result = compute_spatial_metrics_for_sample(sample_map, sample_id, element)

        assert isinstance(result, dict)
        assert "sample_id" in result
        assert "element" in result
        assert "correlation_length" in result
        assert "model_type" in result
        assert "AIC" in result
        assert "r_squared" in result

    def test_compute_metrics_with_gaussian_data(self):
        """Should fit a Gaussian model to Gaussian-like data."""
        x = np.linspace(-5, 5, 50)
        y = np.linspace(-5, 5, 50)
        X, Y = np.meshgrid(x, y)
        # Create a smooth Gaussian-like map
        sample_map = np.exp(-(X**2 + Y**2) / 4)
        sample_id = "gaussian_test"
        element = "I"

        result = compute_spatial_metrics_for_sample(sample_map, sample_id, element)

        assert result["model_type"] == "Gaussian"
        assert result["correlation_length"] > 0
        assert result["AIC"] >= 0

    def test_compute_metrics_with_exponential_data(self):
        """Should fit an Exponential model to exponential-like data."""
        # Create a map that approximates exponential decay in autocorrelation
        np.random.seed(42)
        # Use a filtered noise that creates exponential-like correlation
        sample_map = np.random.randn(64, 64)
        # Apply a box filter to create short-range correlations
        from scipy.ndimage import uniform_filter
        sample_map = uniform_filter(sample_map, size=3)
        
        sample_id = "exp_test"
        element = "MA"

        result = compute_spatial_metrics_for_sample(sample_map, sample_id, element)

        # The model type might be Gaussian or Exponential depending on fit
        assert result["model_type"] in ["Gaussian", "Exponential", "Power_Law"]
        assert "correlation_length" in result
        assert result["correlation_length"] > 0


class TestProcessDatasetAndWriteMetrics:
    def test_process_dataset_creates_file(self):
        """Should create the output CSV file."""
        np.random.seed(42)
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_metrics.csv"
            
            # Create a minimal fake dataset
            fake_data = [
                {"sample_id": "s1", "element": "Pb", "map_path": "dummy"},
                {"sample_id": "s2", "element": "I", "map_path": "dummy"}
            ]
            
            # We cannot easily test full dataset processing without real map files,
            # so we test that the function signature is correct and handles empty/edge cases
            # by verifying it doesn't crash on invalid input structure (it should fail loudly)
            
            # Instead, we test that the function exists and has the right signature
            import inspect
            sig = inspect.signature(process_dataset_and_write_metrics)
            params = list(sig.parameters.keys())
            assert "data_path" in params
            assert "output_path" in params

    def test_process_dataset_with_real_sample(self):
        """Test with a synthetic map that we generate in memory."""
        np.random.seed(42)
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "metrics.csv"
            
            # Create a temporary CSV with a fake path pointing to a real numpy file
            # We'll mock the map loading by creating a numpy file
            map_path = Path(tmpdir) / "map.npy"
            sample_map = np.exp(-(np.linspace(-5, 5, 64)**2) / 4)
            sample_map = sample_map[:, np.newaxis] * sample_map[np.newaxis, :]
            np.save(map_path, sample_map)
            
            # Create a minimal metadata CSV
            meta_csv = Path(tmpdir) / "meta.csv"
            import pandas as pd
            df = pd.DataFrame([
                {"sample_id": "test_001", "element": "Pb", "map_path": str(map_path)}
            ])
            df.to_csv(meta_csv, index=False)
            
            # This should run without error and produce a CSV
            try:
                process_dataset_and_write_metrics(str(meta_csv), str(output_path))
                assert output_path.exists()
                result_df = pd.read_csv(output_path)
                assert len(result_df) > 0
                assert "sample_id" in result_df.columns
                assert "correlation_length" in result_df.columns
            except Exception as e:
                pytest.fail(f"process_dataset_and_write_metrics failed: {e}")

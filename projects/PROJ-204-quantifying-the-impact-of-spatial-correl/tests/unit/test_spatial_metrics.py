"""
Unit tests for spatial metrics analysis module.
"""
import pytest
import numpy as np
from pathlib import Path
import sys
import os
import tempfile

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.analysis.spatial_metrics import (
    gaussian_decay,
    exponential_decay,
    compute_autocorrelation,
    fit_decay_model,
    compute_radial_distances,
    extract_radial_profile,
    compute_spatial_metrics_for_sample
)

class TestGaussianDecay:
    def test_gaussian_decay_basic(self):
        """Test basic Gaussian decay function"""
        x = np.array([0, 1, 2, 3])
        amplitude, sigma, offset = 1.0, 1.0, 0.0
        result = gaussian_decay(x, amplitude, sigma, offset)
        
        # At x=0, should be amplitude + offset = 1.0
        assert np.isclose(result[0], 1.0)
        # At x=1, should be amplitude * exp(-0.5) + offset
        expected = amplitude * np.exp(-0.5) + offset
        assert np.isclose(result[1], expected)

    def test_gaussian_decay_offset(self):
        """Test Gaussian decay with offset"""
        x = np.array([0, 10])
        result = gaussian_decay(x, 2.0, 1.0, 0.5)
        
        # At large x, should approach offset
        assert result[1] > 0.5
        assert result[1] < 0.6

class TestExponentialDecay:
    def test_exponential_decay_basic(self):
        """Test basic exponential decay function"""
        x = np.array([0, 1, 2, 3])
        amplitude, tau, offset = 1.0, 1.0, 0.0
        result = exponential_decay(x, amplitude, tau, offset)
        
        # At x=0, should be amplitude + offset = 1.0
        assert np.isclose(result[0], 1.0)
        # At x=1, should be amplitude * exp(-1) + offset
        expected = amplitude * np.exp(-1) + offset
        assert np.isclose(result[1], expected)

class TestComputeAutocorrelation:
    def test_autocorrelation_shape(self):
        """Test that autocorrelation has same shape as input"""
        data = np.random.randn(10, 10)
        autocorr = compute_autocorrelation(data)
        assert autocorr.shape == data.shape

    def test_autocorrelation_center(self):
        """Test that autocorrelation is maximum at center"""
        # Create a simple pattern with known autocorrelation
        data = np.zeros((20, 20))
        data[10, 10] = 1.0  # Single peak
        autocorr = compute_autocorrelation(data)
        
        # Center should be maximum
        center_y, center_x = autocorr.shape[0] // 2, autocorr.shape[1] // 2
        assert autocorr[center_y, center_x] >= autocorr.max()

    def test_autocorrelation_symmetry(self):
        """Test that autocorrelation is symmetric"""
        data = np.random.randn(15, 15)
        autocorr = compute_autocorrelation(data)
        
        # Autocorrelation should be symmetric around center
        center_y, center_x = autocorr.shape[0] // 2, autocorr.shape[1] // 2
        for dy in range(-5, 6):
            for dx in range(-5, 6):
                y1, x1 = center_y + dy, center_x + dx
                y2, x2 = center_y - dy, center_x - dx
                if 0 <= y1 < autocorr.shape[0] and 0 <= x1 < autocorr.shape[1]:
                    if 0 <= y2 < autocorr.shape[0] and 0 <= x2 < autocorr.shape[1]:
                        assert np.isclose(autocorr[y1, x1], autocorr[y2, x2])

class TestFitDecayModel:
    def test_fit_gaussian_decay(self):
        """Test fitting a Gaussian decay model to synthetic data"""
        # Generate synthetic data with known parameters
        x = np.linspace(0, 20, 50)
        true_amplitude, true_sigma, true_offset = 1.5, 3.0, 0.1
        y = gaussian_decay(x, true_amplitude, true_sigma, true_offset)
        
        # Add small noise
        y_noisy = y + np.random.normal(0, 0.01, len(x))
        
        # Fit model
        params = fit_decay_model(x, y_noisy, 'gaussian')
        
        # Check that fitted parameters are close to true values (within 20%)
        assert abs(params['sigma'] - true_sigma) / true_sigma < 0.2
        assert abs(params['amplitude'] - true_amplitude) / true_amplitude < 0.2

    def test_fit_exponential_decay(self):
        """Test fitting an exponential decay model to synthetic data"""
        # Generate synthetic data with known parameters
        x = np.linspace(0, 20, 50)
        true_amplitude, true_tau, true_offset = 1.5, 3.0, 0.1
        y = exponential_decay(x, true_amplitude, true_tau, true_offset)
        
        # Add small noise
        y_noisy = y + np.random.normal(0, 0.01, len(x))
        
        # Fit model
        params = fit_decay_model(x, y_noisy, 'exponential')
        
        # Check that fitted parameters are close to true values (within 20%)
        assert abs(params['tau'] - true_tau) / true_tau < 0.2
        assert abs(params['amplitude'] - true_amplitude) / true_amplitude < 0.2

    def test_fit_invalid_data(self):
        """Test fitting with invalid data raises error"""
        with pytest.raises(ValueError):
            fit_decay_model(np.array([]), np.array([]), 'gaussian')

class TestComputeRadialDistances:
    def test_radial_distances_shape(self):
        """Test that radial distances have correct shape"""
        shape = (20, 30)
        distances = compute_radial_distances(shape)
        assert distances.shape == shape

    def test_radial_distances_center(self):
        """Test that center has zero distance"""
        shape = (20, 20)
        distances = compute_radial_distances(shape)
        center_y, center_x = shape[0] // 2, shape[1] // 2
        assert distances[center_y, center_x] == 0.0

class TestExtractRadialProfile:
    def test_radial_profile_extraction(self):
        """Test extracting radial profile from a simple autocorrelation"""
        # Create a simple 2D Gaussian
        x, y = np.meshgrid(np.linspace(-5, 5, 20), np.linspace(-5, 5, 20))
        autocorr = np.exp(-(x**2 + y**2) / 2)
        
        distances, profile = extract_radial_profile(autocorr)
        
        # Profile should be decreasing
        assert np.all(np.diff(profile) <= 0.01)  # Allow small numerical errors
        assert len(distances) == len(profile)

class TestComputeSpatialMetricsForSample:
    def test_compute_metrics_gaussian(self):
        """Test computing spatial metrics for a Gaussian-like map"""
        # Create a 2D Gaussian map
        x, y = np.meshgrid(np.linspace(-10, 10, 50), np.linspace(-10, 10, 50))
        true_sigma = 3.0
        map_data = np.exp(-(x**2 + y**2) / (2 * true_sigma**2))
        
        metrics = compute_spatial_metrics_for_sample("test_sample", "Pb", map_data)
        
        assert metrics['sample_id'] == "test_sample"
        assert metrics['element'] == "Pb"
        assert metrics['model_type'] in ['gaussian', 'exponential']
        assert not np.isnan(metrics['correlation_length'])

    def test_compute_metrics_exponential(self):
        """Test computing spatial metrics for an exponential-like map"""
        # Create a 2D exponential map
        x, y = np.meshgrid(np.linspace(-10, 10, 50), np.linspace(-10, 10, 50))
        true_tau = 3.0
        map_data = np.exp(-np.sqrt(x**2 + y**2) / true_tau)
        
        metrics = compute_spatial_metrics_for_sample("test_sample", "I", map_data)
        
        assert metrics['sample_id'] == "test_sample"
        assert metrics['element'] == "I"
        assert metrics['model_type'] in ['gaussian', 'exponential']
        assert not np.isnan(metrics['correlation_length'])

    def test_compute_metrics_invalid(self):
        """Test computing metrics with invalid data"""
        # Create invalid map (all zeros)
        map_data = np.zeros((10, 10))
        
        metrics = compute_spatial_metrics_for_sample("test_sample", "MA", map_data)
        
        # Should handle gracefully and return NaN
        assert metrics['sample_id'] == "test_sample"
        assert metrics['element'] == "MA"
        assert metrics['model_type'] in ['none', 'error']

class TestIntegration:
    def test_end_to_end_with_temp_files(self):
        """Test end-to-end processing with temporary files"""
        import pandas as pd
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test map files
            test_maps = {}
            for element in ['Pb', 'I', 'MA']:
                x, y = np.meshgrid(np.linspace(-5, 5, 20), np.linspace(-5, 5, 20))
                map_data = np.exp(-(x**2 + y**2) / 2)
                map_path = Path(tmpdir) / f"test_{element}.npy"
                np.save(map_path, map_data)
                test_maps[element] = str(map_path)
            
            # Create input CSV
            input_csv = Path(tmpdir) / "input.csv"
            df = pd.DataFrame([{
                'sample_id': 'test_001',
                'Pb_map_path': test_maps['Pb'],
                'I_map_path': test_maps['I'],
                'MA_map_path': test_maps['MA']
            }])
            df.to_csv(input_csv, index=False)
            
            # Run processing
            output_csv = Path(tmpdir) / "output.csv"
            from code.analysis.spatial_metrics import process_dataset_and_write_metrics
            process_dataset_and_write_metrics(str(input_csv), str(output_csv))
            
            # Check output
            assert output_csv.exists()
            output_df = pd.read_csv(output_csv)
            assert len(output_df) == 3  # 3 elements
            assert 'correlation_length' in output_df.columns
            assert 'model_type' in output_df.columns
            assert 'AIC' in output_df.columns
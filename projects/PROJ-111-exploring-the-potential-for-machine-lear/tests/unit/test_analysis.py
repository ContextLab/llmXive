import os
import sys
import unittest
import numpy as np
import tempfile
import json

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from analysis import (
    load_latent_data,
    calculate_total_variance_per_bin,
    smooth_and_detect_peak,
    save_variance_results
)

class TestAnalysis(unittest.TestCase):

    def setUp(self):
        """Create temporary directory and mock data for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.mock_data_path = os.path.join(self.temp_dir, "mock_latent.npz")
        
        # Create mock latent data
        # Temperatures: 0.1 to 3.0
        temps = np.linspace(0.1, 3.0, 30)
        # Latent dim = 10
        latent_dim = 10
        # Generate synthetic variance pattern: peak around T=1.5
        mu_data = []
        for t in temps:
            # Create a distribution that has higher variance near T=1.5
            # We simulate samples for this temperature
            n_samples = 50
            # Mean shifts slightly, variance changes
            base_var = 0.01 + 0.5 * np.exp(-((t - 1.5) / 0.5) ** 2)
            samples = np.random.normal(0, np.sqrt(base_var), size=(n_samples, latent_dim))
            mu_data.append(samples)
        
        mu_all = np.vstack(mu_data)
        temps_all = np.repeat(temps, 50)
        
        np.savez(self.mock_data_path, temperatures=temps_all, mu=mu_all)

    def tearDown(self):
        """Clean up temporary files."""
        if os.path.exists(self.mock_data_path):
            os.remove(self.mock_data_path)
        os.rmdir(self.temp_dir)

    def test_load_latent_data(self):
        """Test loading latent data from .npz file."""
        data = load_latent_data(self.mock_data_path)
        self.assertIn('temperatures', data)
        self.assertIn('mu', data)
        self.assertEqual(data['temperatures'].shape[0], len(temps_all))
        self.assertEqual(data['mu'].shape[0], len(temps_all))
        self.assertEqual(data['mu'].shape[1], 10)

    def test_calculate_total_variance_per_bin(self):
        """Test variance calculation per temperature bin."""
        data = load_latent_data(self.mock_data_path)
        temps, variances = calculate_total_variance_per_bin(data)
        
        self.assertEqual(len(temps), 30) # 30 unique temperatures
        self.assertEqual(len(variances), 30)
        
        # Check that variance is higher around T=1.5
        idx_peak = np.argmin(np.abs(temps - 1.5))
        idx_low = np.argmin(np.abs(temps - 0.5))
        self.assertGreater(variances[idx_peak], variances[idx_low])

    def test_smooth_and_detect_peak_curvature(self):
        """Test peak detection with curvature condition."""
        # Generate data with a clear peak
        temps = np.linspace(0.1, 3.0, 50)
        # Create a Gaussian peak
        peak_t = 1.5
        width = 0.3
        variances = 0.01 + 1.0 * np.exp(-((temps - peak_t) / width) ** 2)
        
        result = smooth_and_detect_peak(
            temperatures=temps,
            variances=variances,
            kernel_lengthscale=0.2,
            second_derivative_threshold=-0.01,
            moving_avg_window=5,
            sigma_threshold_factor=2.0
        )
        
        self.assertIn('peak_temperature', result)
        self.assertIn('peak_value', result)
        self.assertTrue(result['peak_found_by_curvature'])
        
        # Check if detected peak is close to 1.5
        self.assertAlmostEqual(result['peak_temperature'], peak_t, delta=0.2)

    def test_smooth_and_detect_peak_height_condition(self):
        """Test peak detection with height condition (2 sigma above MA of residuals)."""
        # Same setup as above
        temps = np.linspace(0.1, 3.0, 50)
        peak_t = 1.5
        width = 0.3
        variances = 0.01 + 1.0 * np.exp(-((temps - peak_t) / width) ** 2)
        
        result = smooth_and_detect_peak(
            temperatures=temps,
            variances=variances,
            kernel_lengthscale=0.2,
            second_derivative_threshold=-0.01,
            moving_avg_window=5,
            sigma_threshold_factor=2.0
        )
        
        self.assertIn('criteria_met', result)
        self.assertEqual(result['criteria_met']['sigma_threshold'], 2.0)
        self.assertEqual(result['criteria_met']['window_size'], 5)

    def test_save_variance_results(self):
        """Test saving results to JSON."""
        results = {
            'input_file': 'test.npz',
            'temperature_bins': [0.1, 0.2],
            'variances': [0.5, 0.6],
            'peak_detection': {
                'peak_temperature': 1.5,
                'peak_value': 1.0,
                'smoothed_variance': [0.5, 0.6],
                'peak_found_by_curvature': True
            }
        }
        
        output_path = os.path.join(self.temp_dir, "results.json")
        save_variance_results(results, output_path)
        
        self.assertTrue(os.path.exists(output_path))
        
        with open(output_path, 'r') as f:
            loaded = json.load(f)
        
        self.assertEqual(loaded['peak_detection']['peak_temperature'], 1.5)

if __name__ == '__main__':
    unittest.main()

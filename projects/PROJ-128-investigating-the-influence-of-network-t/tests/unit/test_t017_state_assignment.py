"""
Unit tests for Task T017: LOO State Assignment and Dynamic Metrics Calculation.
"""

import os
import sys
import numpy as np
import pandas as pd
import tempfile
import unittest
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from preprocess.functional_t017 import (
    load_loo_centroids,
    compute_sliding_window_correlation,
    assign_states_and_calculate_metrics,
    main
)

class TestT017StateAssignment(unittest.TestCase):

    def setUp(self):
        """Set up temporary directory and mock data."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_path = Path(self.temp_dir.name)
        
        # Create mock LOO centroids
        # Format: subject_001_centroids -> (5, n_features)
        # We need to determine n_features based on regions.
        # Let's assume 10 regions -> 10*9/2 = 45 features (upper triangle)
        self.n_regions = 10
        self.n_features = self.n_regions * (self.n_regions - 1) // 2
        self.k = 5
        
        self.centroids = {}
        for i in range(1, 4): # 3 subjects
            key = f"subject_{i:03d}_centroids"
            self.centroids[key] = np.random.rand(self.k, self.n_features)
        
        # Save to npz
        self.centroids_path = self.output_path / "loo_centroids_all_subjects.npz"
        np.savez(str(self.centroids_path), **self.centroids)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_loo_centroids_success(self):
        """Test loading centroids from a valid file."""
        loaded = load_loo_centroids(str(self.centroids_path))
        self.assertEqual(len(loaded), 3)
        self.assertIn("subject_001_centroids", loaded)
        self.assertEqual(loaded["subject_001_centroids"].shape, (self.k, self.n_features))

    def test_load_loo_centroids_missing_file(self):
        """Test loading from a non-existent file raises error."""
        with self.assertRaises(FileNotFoundError):
            load_loo_centroids("non_existent_path.npz")

    def test_compute_sliding_window_correlation(self):
        """Test sliding window correlation calculation."""
        # Create mock fMRI data: 100 time points, 10 regions
        fmri_data = np.random.rand(100, self.n_regions)
        window_length = 10
        step = 1
        
        windows = compute_sliding_window_correlation(fmri_data, window_length, step)
        
        # Expected number of windows: (100 - 10) / 1 + 1 = 91
        self.assertEqual(len(windows), 91)
        self.assertEqual(windows[0].shape, (self.n_regions, self.n_regions))
        
        # Verify symmetry
        self.assertTrue(np.allclose(windows[0], windows[0].T))

    def test_assign_states_and_calculate_metrics(self):
        """Test state assignment and metric calculation logic."""
        # Mock fMRI data: 50 time points, 10 regions
        fmri_data = np.random.rand(50, self.n_regions)
        
        # Load centroids
        centroids_dict = load_loo_centroids(str(self.centroids_path))
        
        state_df, metrics = assign_states_and_calculate_metrics(
            subject_id="001",
            centroids_dict=centroids_dict,
            fmri_data=fmri_data,
            window_length=10,
            step=1
        )
        
        # Check state_df structure
        self.assertIn('subject_id', state_df.columns)
        self.assertIn('window_index', state_df.columns)
        self.assertIn('state_id', state_df.columns)
        self.assertEqual(len(state_df), 41) # 50 - 10 + 1
        self.assertTrue(all(state_df['subject_id'] == "001"))
        
        # Check metrics structure
        self.assertIn('subject_id', metrics)
        self.assertIn('state_id', metrics)
        self.assertIn('mean_dwell_time', metrics)
        self.assertIn('num_visits', metrics)
        
        # Verify metrics are numeric and reasonable
        self.assertEqual(len(metrics['state_id']), self.k)
        self.assertTrue(all(isinstance(m, (int, float)) for m in metrics['mean_dwell_time']))
        self.assertTrue(all(isinstance(v, int) for v in metrics['num_visits']))

    def test_state_assignment_consistency(self):
        """Test that identical inputs produce identical outputs."""
        fmri_data = np.random.rand(50, self.n_regions)
        centroids_dict = load_loo_centroids(str(self.centroids_path))
        
        # Run twice
        df1, met1 = assign_states_and_calculate_metrics("001", centroids_dict, fmri_data, 10, 1)
        df2, met2 = assign_states_and_calculate_metrics("001", centroids_dict, fmri_data, 10, 1)
        
        # Compare
        pd.testing.assert_frame_equal(df1, df2)
        self.assertEqual(met1, met2)

    def test_empty_window_list(self):
        """Test that short time series raises error."""
        # Time series shorter than window length
        fmri_data = np.random.rand(5, self.n_regions) # 5 < 10
        centroids_dict = load_loo_centroids(str(self.centroids_path))
        
        with self.assertRaises(ValueError):
            assign_states_and_calculate_metrics("001", centroids_dict, fmri_data, 10, 1)

if __name__ == '__main__':
    unittest.main()
"""
Tests for Task T010: Compute Pilot Correlation
"""

import os
import tempfile
import json
from pathlib import Path
import unittest
import pandas as pd
import numpy as np

# Mock the config import if running in isolation, but rely on real config in full run
# For this test file, we assume src.config is available or mock it
import sys
from unittest.mock import patch, MagicMock

# We will patch the config functions to return temporary paths for testing
def mock_get_relative_path(path_str):
    return str(Path(tempfile.gettempdir()) / path_str)

@patch('src.metrics.validate.get_relative_path', mock_get_relative_path)
class TestCorrelationCalculation(unittest.TestCase):
    
    def setUp(self):
        """Setup temporary files and mock data."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.human_ratings_path = self.temp_dir / "human_ratings.csv"
        self.metrics_path = self.temp_dir / "metrics.csv"
        self.output_path = self.temp_dir / "correlation_results.json"
        
        # Create mock human ratings data
        # Multiple participants rating the same images
        human_data = {
            'image_id': ['img1', 'img1', 'img2', 'img2', 'img3', 'img3', 'img4', 'img4'],
            'participant_id': ['p1', 'p2', 'p1', 'p2', 'p1', 'p2', 'p1', 'p2'],
            'complexity_score': [1.0, 1.2, 3.0, 2.8, 5.0, 5.1, 2.0, 2.1]
        }
        self.human_df = pd.DataFrame(human_data)
        self.human_df.to_csv(self.human_ratings_path, index=False)
        
        # Create mock metrics data
        # Correlating perfectly with the mean human scores
        # img1 (mean ~1.1) -> low entropy
        # img2 (mean ~2.9) -> med entropy
        # img3 (mean ~5.05) -> high entropy
        # img4 (mean ~2.05) -> low-med entropy
        metrics_data = {
            'image_id': ['img1', 'img2', 'img3', 'img4'],
            'entropy': [1.0, 3.0, 5.0, 2.0],
            'color_variance': [0.5, 1.5, 2.5, 1.0],
            'object_count': [1, 2, 3, 1]
        }
        self.metrics_df = pd.DataFrame(metrics_data)
        self.metrics_df.to_csv(self.metrics_path, index=False)

    def tearDown(self):
        """Cleanup temporary files."""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    @patch('src.metrics.validate.get_relative_path')
    @patch('src.metrics.validate.PATHS') # Ensure we patch where it's used if needed, but we use direct paths in test
    def test_correlation_calculation(self, mock_get_path):
        """
        Test that the correlation calculation function correctly computes Pearson r
        and p-values between human ratings and automated metrics.
        """
        # Setup mock for get_relative_path to return our temp paths
        def side_effect(path_str):
            if "human_ratings" in path_str:
                return str(self.human_ratings_path)
            elif "metrics" in path_str:
                return str(self.metrics_path)
            elif "pilot_correlation" in path_str:
                return str(self.output_path)
            return str(self.temp_dir / path_str)
        
        mock_get_path.side_effect = side_effect

        # Import the functions under test (re-import to pick up mocks if needed, 
        # but here we test the logic directly by calling the functions with DataFrames)
        from src.metrics.validate import compute_correlations, load_human_ratings, load_metrics, write_report
        
        # Test loading
        loaded_human = load_human_ratings()
        loaded_metrics = load_metrics()
        
        self.assertEqual(len(loaded_human), 8)
        self.assertEqual(len(loaded_metrics), 4)
        
        # Test computation
        results = compute_correlations(loaded_human, loaded_metrics)
        
        # Check that results are returned for all metrics
        self.assertIn('entropy', results)
        self.assertIn('color_variance', results)
        self.assertIn('object_count', results)
        
        # Check status
        self.assertEqual(results['entropy']['status'], 'success')
        
        # Verify correlation logic:
        # Human means: img1=1.1, img2=2.9, img3=5.05, img4=2.05
        # Entropy: 1.0, 3.0, 5.0, 2.0
        # These are perfectly correlated (r should be 1.0)
        self.assertAlmostEqual(results['entropy']['r'], 1.0, places=5)
        self.assertLess(results['entropy']['p_value'], 0.05) # Significant
        
        # Check sample count
        self.assertEqual(results['entropy']['n_samples'], 4)

    @patch('src.metrics.validate.get_relative_path')
    def test_correlation_with_missing_data(self, mock_get_path):
        """Test handling of missing values in metrics."""
        def side_effect(path_str):
            if "human_ratings" in path_str:
                return str(self.human_ratings_path)
            elif "metrics" in path_str:
                # Create a metrics file with a NaN
                temp_metrics = self.temp_dir / "metrics_nan.csv"
                metrics_data = {
                    'image_id': ['img1', 'img2', 'img3', 'img4'],
                    'entropy': [1.0, np.nan, 5.0, 2.0],
                    'color_variance': [0.5, 1.5, 2.5, 1.0],
                    'object_count': [1, 2, 3, 1]
                }
                pd.DataFrame(metrics_data).to_csv(temp_metrics, index=False)
                return str(temp_metrics)
            elif "pilot_correlation" in path_str:
                return str(self.output_path)
            return str(self.temp_dir / path_str)
        
        mock_get_path.side_effect = side_effect

        from src.metrics.validate import load_human_ratings, load_metrics, compute_correlations
        
        human_df = load_human_ratings()
        metrics_df = load_metrics()
        
        results = compute_correlations(human_df, metrics_df)
        
        # entropy should have fewer samples due to NaN
        self.assertLess(results['entropy']['n_samples'], 4)
        self.assertEqual(results['entropy']['status'], 'success')
        
        # Other metrics should still have 4 samples
        self.assertEqual(results['color_variance']['n_samples'], 4)

    @patch('src.metrics.validate.get_relative_path')
    def test_write_report(self, mock_get_path):
        """Test that the report is written correctly to disk."""
        def side_effect(path_str):
            if "human_ratings" in path_str:
                return str(self.human_ratings_path)
            elif "metrics" in path_str:
                return str(self.metrics_path)
            elif "pilot_correlation" in path_str:
                return str(self.output_path)
            return str(self.temp_dir / path_str)
        
        mock_get_path.side_effect = side_effect

        from src.metrics.validate import load_human_ratings, load_metrics, compute_correlations, write_report
        
        human_df = load_human_ratings()
        metrics_df = load_metrics()
        results = compute_correlations(human_df, metrics_df)
        
        write_report(results)
        
        self.assertTrue(self.output_path.exists())
        
        with open(self.output_path, 'r') as f:
            saved_results = json.load(f)
        
        self.assertEqual(saved_results['entropy']['status'], 'success')
        self.assertAlmostEqual(saved_results['entropy']['r'], 1.0, places=5)

    @patch('src.metrics.validate.get_relative_path')
    def test_insufficient_data(self, mock_get_path):
        """Test behavior when there is insufficient data (less than 2 points)."""
        # Create a scenario with only 1 matching image
        temp_human = self.temp_dir / "human_small.csv"
        pd.DataFrame({
            'image_id': ['img1', 'img1'],
            'participant_id': ['p1', 'p2'],
            'complexity_score': [1.0, 1.2]
        }).to_csv(temp_human, index=False)
        
        temp_metrics = self.temp_dir / "metrics_small.csv"
        pd.DataFrame({
            'image_id': ['img1'],
            'entropy': [1.0],
            'color_variance': [0.5],
            'object_count': [1]
        }).to_csv(temp_metrics, index=False)
        
        def side_effect(path_str):
            if "human_ratings" in path_str:
                return str(temp_human)
            elif "metrics" in path_str:
                return str(temp_metrics)
            elif "pilot_correlation" in path_str:
                return str(self.output_path)
            return str(self.temp_dir / path_str)
        
        mock_get_path.side_effect = side_effect

        from src.metrics.validate import load_human_ratings, load_metrics, compute_correlations
        
        human_df = load_human_ratings()
        metrics_df = load_metrics()
        
        results = compute_correlations(human_df, metrics_df)
        
        self.assertEqual(results['entropy']['status'], 'insufficient_data')
        self.assertTrue(np.isnan(results['entropy']['r']))
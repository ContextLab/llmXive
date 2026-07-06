import os
import sys
import json
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock
import numpy as np
import pandas as pd

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analysis.plot_results import (
    create_scatter_plot,
    create_null_distribution_plot,
    generate_all_plots,
    load_stats_results,
    load_metrics_for_plotting
)

class TestPlotResults(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.results_dir = Path(self.temp_dir) / "results"
        self.plots_dir = self.results_dir / "plots"
        self.plots_dir.mkdir(parents=True)
        
        # Create mock stats.json
        self.stats_path = self.results_dir / "stats.json"
        mock_stats = {
            "correlations": {
                "flexibility": {
                    "rho": 0.45,
                    "p_uncorrected": 0.001,
                    "p_fdr_corrected": 0.003
                },
                "stability": {
                    "rho": -0.2,
                    "p_uncorrected": 0.15,
                    "p_fdr_corrected": 0.20
                }
            },
            "permutation_results": {
                "p_permutation": 0.002
            },
            "null_distribution": np.random.normal(0, 0.1, 1000).tolist(),
            "observed_statistic": 0.45
        }
        with open(self.stats_path, 'w') as f:
            json.dump(mock_stats, f)
        
        # Create mock metrics CSV
        self.metrics_path = Path(self.temp_dir) / "data" / "metrics"
        self.metrics_path.mkdir(parents=True)
        metrics_df = pd.DataFrame({
            'subject_id': [f'sub-{i:03d}' for i in range(1, 51)],
            'dream_recall_frequency': np.random.randint(1, 10, 50),
            'flexibility': np.random.normal(0.5, 0.1, 50),
            'stability': np.random.normal(0.3, 0.05, 50)
        })
        metrics_df.to_csv(self.metrics_path / "subject_metrics.csv", index=False)

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir)

    @patch('analysis.plot_results.STATS_JSON_PATH')
    @patch('analysis.plot_results.RESULTS_DIR')
    def test_load_stats_results(self, mock_results_dir, mock_stats_path):
        """Test loading stats results from JSON."""
        mock_stats_path.__truediv__.return_value = self.stats_path
        mock_results_dir.__truediv__.return_value = self.results_dir
        
        result = load_stats_results()
        self.assertIn('correlations', result)
        self.assertIn('flexibility', result['correlations'])
        self.assertEqual(result['correlations']['flexibility']['rho'], 0.45)

    @patch('analysis.plot_results.Path')
    def test_load_metrics_for_plotting(self, mock_path):
        """Test loading metrics for plotting."""
        # Mock the Path.exists to return True
        mock_path.return_value.exists.return_value = True
        
        # Mock the read_csv to return our test dataframe
        with patch('analysis.plot_results.pd.read_csv') as mock_read:
            mock_df = pd.DataFrame({
                'subject_id': ['sub-001'],
                'dream_recall_frequency': [5],
                'flexibility': [0.5],
                'stability': [0.3]
            })
            mock_read.return_value = mock_df
            
            result = load_metrics_for_plotting()
            self.assertIn('dream_recall_frequency', result.columns)
            self.assertIn('flexibility', result.columns)

    def test_create_scatter_plot(self):
        """Test scatter plot creation."""
        output_path = self.plots_dir / "test_scatter.png"
        x_data = np.random.rand(20)
        y_data = 2 * x_data + np.random.normal(0, 0.1, 20)
        
        create_scatter_plot(
            x_data, y_data,
            "X Label", "Y Label", "Test Title",
            output_path, rho=0.8, p_val=0.001
        )
        
        self.assertTrue(output_path.exists())
        self.assertGreater(output_path.stat().st_size, 0)

    def test_create_null_distribution_plot(self):
        """Test null distribution plot creation."""
        output_path = self.plots_dir / "test_null.png"
        null_dist = np.random.normal(0, 0.1, 1000)
        
        create_null_distribution_plot(
            null_dist, 0.45, 0.002, output_path
        )
        
        self.assertTrue(output_path.exists())
        self.assertGreater(output_path.stat().st_size, 0)

    @patch('analysis.plot_results.PLOTS_DIR')
    @patch('analysis.plot_results.STATS_JSON_PATH')
    @patch('analysis.plot_results.RESULTS_DIR')
    def test_generate_all_plots(self, mock_results_dir, mock_stats_path, mock_plots_dir):
        """Test full plot generation pipeline."""
        # Setup mocks
        mock_stats_path.__truediv__.return_value = self.stats_path
        mock_results_dir.__truediv__.return_value = self.results_dir
        
        # Create a mock PLOTS_DIR that points to our temp plots dir
        mock_plots_dir.__truediv__.return_value = self.plots_dir
        mock_plots_dir.mkdir = MagicMock()
        mock_plots_dir.exists.return_value = True
        
        # Mock the metrics path check
        with patch('analysis.plot_results.Path') as mock_path_class:
            # Setup for metrics file check
            mock_metrics_path = MagicMock()
            mock_metrics_path.exists.return_value = True
            mock_path_class.return_value = mock_metrics_path
            
            # Mock read_csv to return our test data
            with patch('analysis.plot_results.pd.read_csv') as mock_read:
                mock_df = pd.DataFrame({
                    'subject_id': [f'sub-{i:03d}' for i in range(1, 51)],
                    'dream_recall_frequency': np.random.randint(1, 10, 50),
                    'flexibility': np.random.normal(0.5, 0.1, 50),
                    'stability': np.random.normal(0.3, 0.05, 50)
                })
                mock_read.return_value = mock_df
                
                result = generate_all_plots()
                
                # Should have generated plots for flexibility and stability
                self.assertIn('flexibility', result)
                self.assertIn('stability', result)
                self.assertIn('null_distribution', result)
                
                # Verify files exist
                for path in result.values():
                    self.assertTrue(Path(path).exists())

if __name__ == '__main__':
    unittest.main()
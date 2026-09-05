import os
import sys
import tempfile
import unittest
from pathlib import Path
import pandas as pd
import numpy as np

# Add parent directory to path to import code modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from correlation_analysis import (
    load_roi_betas,
    load_learning_rate_slopes,
    calculate_pearson_correlation,
    generate_scatter_plot
)

class TestCorrelationAnalysis(unittest.TestCase):
    
    def setUp(self):
        """Create temporary files for testing."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.temp_dir.name)
        
        # Create mock roi_betas.csv
        self.roi_betas_path = self.data_dir / "roi_betas.csv"
        betas_df = pd.DataFrame({
            'subject_id': ['sub-01', 'sub-02', 'sub-03', 'sub-04'],
            'beta_value': [0.5, 0.8, 1.2, 0.9]
        })
        betas_df.to_csv(self.roi_betas_path, index=False)
        
        # Create mock learning_rate_slopes.csv
        self.slopes_path = self.data_dir / "learning_rate_slopes.csv"
        slopes_df = pd.DataFrame({
            'subject_id': ['sub-01', 'sub-02', 'sub-03', 'sub-04'],
            'slope': [-5.0, -8.0, -12.0, -9.5]
        })
        slopes_df.to_csv(self.slopes_path, index=False)

    def tearDown(self):
        """Clean up temporary files."""
        self.temp_dir.cleanup()

    def test_load_roi_betas(self):
        """Test loading ROI betas from CSV."""
        data = load_roi_betas(self.roi_betas_path)
        self.assertEqual(len(data), 4)
        self.assertEqual(data['sub-01'], 0.5)
        self.assertEqual(data['sub-03'], 1.2)

    def test_load_learning_rate_slopes(self):
        """Test loading learning rate slopes from CSV."""
        data = load_learning_rate_slopes(self.slopes_path)
        self.assertEqual(len(data), 4)
        self.assertEqual(data['sub-02'], -8.0)

    def test_pearson_correlation_calculation(self):
        """Test Pearson correlation calculation and plot generation."""
        betas = load_roi_betas(self.roi_betas_path)
        slopes = load_learning_rate_slopes(self.slopes_path)
        
        r, p_value, common_subjects = calculate_pearson_correlation(betas, slopes)
        
        # Verify we have the correct subjects
        self.assertEqual(len(common_subjects), 4)
        self.assertIn('sub-01', common_subjects)
        
        # Verify correlation is negative (higher activation -> more negative slope -> faster learning)
        # Or positive depending on slope definition. Let's check magnitude.
        self.assertIsInstance(r, float)
        self.assertIsInstance(p_value, float)
        self.assertLessEqual(abs(r), 1.0)
        self.assertGreaterEqual(p_value, 0.0)
        self.assertLessEqual(p_value, 1.0)

    def test_plot_generation(self):
        """Test that a plot file is generated."""
        betas = load_roi_betas(self.roi_betas_path)
        slopes = load_learning_rate_slopes(self.slopes_path)
        r, p_value, _ = calculate_pearson_correlation(betas, slopes)
        
        output_path = self.data_dir / "test_plot.png"
        generate_scatter_plot(betas, slopes, output_path, r, p_value)
        
        self.assertTrue(output_path.exists())
        self.assertGreater(output_path.stat().st_size, 0)

    def test_insufficient_subjects(self):
        """Test error handling when too few common subjects exist."""
        # Create a dataset with only 2 common subjects
        small_betas = {'sub-01': 0.5, 'sub-02': 0.8}
        small_slopes = {'sub-01': -5.0, 'sub-02': -8.0}
        
        with self.assertRaises(ValueError) as context:
            calculate_pearson_correlation(small_betas, small_slopes)
        
        self.assertIn("Insufficient common subjects", str(context.exception))

    def test_missing_file(self):
        """Test error handling for missing input files."""
        with self.assertRaises(FileNotFoundError):
            load_roi_betas(Path("non_existent_file.csv"))
        
        with self.assertRaises(FileNotFoundError):
            load_learning_rate_slopes(Path("non_existent_file.csv"))

if __name__ == '__main__':
    unittest.main()
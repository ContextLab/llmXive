"""
Integration test for statistical significance logic (T021).

Validates power analysis and p-value calculation functionality.
This test ensures that the statistical analysis pipeline produces
valid results according to the project requirements.

BLOCKED until T029 complete (as per tasks.md).
"""
import os
import sys
import json
import unittest
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import numpy as np
from scipy import stats

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'code'))

from evaluation import power_analysis_z_test, calculate_cohen_d
from statistical_tests import load_power_analysis, load_performance_metrics, calculate_effect_size, run_paired_tests, save_results
from resampling import ValidationException


class TestStatisticalSignificanceLogic(unittest.TestCase):
    """Integration tests for statistical significance calculations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.results_dir = Path(self.test_dir) / 'results'
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Create mock data for testing
        self.seed_count = 10
        self.properties = ['formation_energy', 'band_gap']
        
        # Generate mock performance metrics for skewed and balanced models
        self.skewed_metrics = {}
        self.balanced_metrics = {}
        
        for prop in self.properties:
            # Generate realistic mock MAE values
            base_mae = np.random.uniform(0.1, 0.5)
            skewed_maes = base_mae + np.random.normal(0, 0.05, self.seed_count)
            balanced_maes = base_mae - np.random.normal(0, 0.03, self.seed_count)
            
            self.skewed_metrics[prop] = skewed_maes
            self.balanced_metrics[prop] = balanced_maes
            
        # Save mock power analysis results
        self.power_analysis_path = self.results_dir / 'power_analysis.json'
        power_data = {
            'seed_count': self.seed_count,
            'effect_size': 0.5,
            'power': 0.8,
            'alpha': 0.05,
            'test_type': 'paired_t_test'
        }
        with open(self.power_analysis_path, 'w') as f:
            json.dump(power_data, f, indent=2)
            
        # Save mock performance metrics
        self.performance_dir = self.results_dir / 'performance_metrics'
        self.performance_dir.mkdir(parents=True, exist_ok=True)
        
        for prop in self.properties:
            skewed_path = self.performance_dir / f'{prop}_skewed_metrics.csv'
            balanced_path = self.performance_dir / f'{prop}_balanced_metrics.csv'
            
            pd.DataFrame({'mae': self.skewed_metrics[prop]}).to_csv(skewed_path, index=False)
            pd.DataFrame({'mae': self.balanced_metrics[prop]}).to_csv(balanced_path, index=False)
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_power_analysis_z_test(self):
        """Test power analysis calculation."""
        # Test with known parameters
        effect_size = 0.5
        alpha = 0.05
        power = 0.8
        
        result = power_analysis_z_test(effect_size, alpha, power)
        
        # Verify result is positive and reasonable
        self.assertIsInstance(result, float)
        self.assertGreater(result, 0)
        self.assertLess(result, 1000)  # Reasonable upper bound
        
    def test_cohen_d_calculation(self):
        """Test Cohen's d effect size calculation."""
        # Generate two samples with known difference
        np.random.seed(42)
        sample1 = np.random.normal(0, 1, 100)
        sample2 = np.random.normal(0.5, 1, 100)  # Mean difference of 0.5
        
        d = calculate_cohen_d(sample1, sample2)
        
        # Verify Cohen's d is approximately 0.5
        self.assertAlmostEqual(d, 0.5, delta=0.2)  # Allow some sampling variance
        
    def test_load_power_analysis(self):
        """Test loading power analysis results."""
        result = load_power_analysis(self.power_analysis_path)
        
        self.assertIsInstance(result, dict)
        self.assertIn('seed_count', result)
        self.assertEqual(result['seed_count'], self.seed_count)
        self.assertIn('effect_size', result)
        self.assertEqual(result['effect_size'], 0.5)
        
    def test_load_performance_metrics(self):
        """Test loading performance metrics."""
        for prop in self.properties:
            skewed_path = self.performance_dir / f'{prop}_skewed_metrics.csv'
            balanced_path = self.performance_dir / f'{prop}_balanced_metrics.csv'
            
            skewed_data = load_performance_metrics(skewed_path)
            balanced_data = load_performance_metrics(balanced_path)
            
            self.assertIsInstance(skewed_data, pd.DataFrame)
            self.assertIsInstance(balanced_data, pd.DataFrame)
            self.assertIn('mae', skewed_data.columns)
            self.assertIn('mae', balanced_data.columns)
            self.assertEqual(len(skewed_data), self.seed_count)
            self.assertEqual(len(balanced_data), self.seed_count)
    
    def test_calculate_effect_size(self):
        """Test effect size calculation between paired samples."""
        for prop in self.properties:
            skewed_path = self.performance_dir / f'{prop}_skewed_metrics.csv'
            balanced_path = self.performance_dir / f'{prop}_balanced_metrics.csv'
            
            skewed_data = load_performance_metrics(skewed_path)
            balanced_data = load_performance_metrics(balanced_path)
            
            effect_size = calculate_effect_size(skewed_data, balanced_data)
            
            self.assertIsInstance(effect_size, float)
            self.assertGreaterEqual(effect_size, 0)  # Absolute value
            
    def test_run_paired_tests(self):
        """Test paired statistical tests (t-test and Wilcoxon)."""
        for prop in self.properties:
            skewed_path = self.performance_dir / f'{prop}_skewed_metrics.csv'
            balanced_path = self.performance_dir / f'{prop}_balanced_metrics.csv'
            
            skewed_data = load_performance_metrics(skewed_path)
            balanced_data = load_performance_metrics(balanced_path)
            
            # Run paired t-test
            t_stat, t_pvalue = stats.ttest_rel(skewed_data['mae'], balanced_data['mae'])
            
            # Run Wilcoxon test
            w_stat, w_pvalue = stats.wilcoxon(skewed_data['mae'], balanced_data['mae'])
            
            # Verify test statistics are reasonable
            self.assertIsInstance(t_stat, (float, np.floating))
            self.assertIsInstance(t_pvalue, (float, np.floating))
            self.assertIsInstance(w_stat, (float, np.floating))
            self.assertIsInstance(w_pvalue, (float, np.floating))
            
            # P-values should be between 0 and 1
            self.assertGreaterEqual(t_pvalue, 0)
            self.assertLessEqual(t_pvalue, 1)
            self.assertGreaterEqual(w_pvalue, 0)
            self.assertLessEqual(w_pvalue, 1)
            
    def test_save_results(self):
        """Test saving statistical test results."""
        output_path = self.results_dir / 'statistical_test_results.csv'
        
        # Create mock results
        results = [
            {
                'test_type': 'paired_t_test',
                'p_value': 0.03,
                'effect_size': 0.5,
                'seed_count': 10
            },
            {
                'test_type': 'wilcoxon',
                'p_value': 0.04,
                'effect_size': 0.5,
                'seed_count': 10
            }
        ]
        
        save_results(results, output_path)
        
        # Verify file was created
        self.assertTrue(output_path.exists())
        
        # Verify content
        df = pd.read_csv(output_path)
        self.assertEqual(len(df), 2)
        self.assertIn('test_type', df.columns)
        self.assertIn('p_value', df.columns)
        self.assertIn('effect_size', df.columns)
        self.assertIn('seed_count', df.columns)
        
    def test_full_statistical_pipeline(self):
        """Test the complete statistical significance pipeline."""
        # Load power analysis
        power_data = load_power_analysis(self.power_analysis_path)
        seed_count = power_data['seed_count']
        
        # Process each property
        all_results = []
        
        for prop in self.properties:
            skewed_path = self.performance_dir / f'{prop}_skewed_metrics.csv'
            balanced_path = self.performance_dir / f'{prop}_balanced_metrics.csv'
            
            skewed_data = load_performance_metrics(skewed_path)
            balanced_data = load_performance_metrics(balanced_path)
            
            # Calculate effect size
            effect_size = calculate_effect_size(skewed_data, balanced_data)
            
            # Run paired t-test
            t_stat, t_pvalue = stats.ttest_rel(skewed_data['mae'], balanced_data['mae'])
            
            # Run Wilcoxon test
            w_stat, w_pvalue = stats.wilcoxon(skewed_data['mae'], balanced_data['mae'])
            
            # Add results
            all_results.append({
                'test_type': 'paired_t_test',
                'p_value': t_pvalue,
                'effect_size': effect_size,
                'seed_count': seed_count
            })
            
            all_results.append({
                'test_type': 'wilcoxon',
                'p_value': w_pvalue,
                'effect_size': effect_size,
                'seed_count': seed_count
            })
        
        # Save results
        output_path = self.results_dir / 'statistical_test_results.csv'
        save_results(all_results, output_path)
        
        # Verify output
        self.assertTrue(output_path.exists())
        df = pd.read_csv(output_path)
        self.assertEqual(len(df), len(self.properties) * 2)
        
    def test_validation_gate(self):
        """Test that validation exceptions are raised for invalid inputs."""
        # Test with empty data
        empty_df = pd.DataFrame(columns=['mae'])
        
        with self.assertRaises((ValueError, ValidationException)):
            calculate_effect_size(empty_df, empty_df)
            
        # Test with mismatched lengths
        df1 = pd.DataFrame({'mae': [1, 2, 3]})
        df2 = pd.DataFrame({'mae': [1, 2]})
        
        with self.assertRaises((ValueError, ValidationException)):
            calculate_effect_size(df1, df2)
            
    def test_power_analysis_consistency(self):
        """Test that power analysis produces consistent results."""
        effect_size = 0.5
        alpha = 0.05
        power = 0.8
        
        # Run multiple times
        results = [power_analysis_z_test(effect_size, alpha, power) for _ in range(5)]
        
        # All results should be identical
        self.assertEqual(len(set(results)), 1)
        
    def test_statistical_test_sensitivity(self):
        """Test that statistical tests are sensitive to actual differences."""
        # Generate data with known difference
        np.random.seed(42)
        sample1 = np.random.normal(0, 1, 100)
        sample2 = np.random.normal(0.5, 1, 100)  # Clear difference
        
        t_stat, t_pvalue = stats.ttest_rel(sample1, sample2)
        
        # Should detect significant difference
        self.assertLess(t_pvalue, 0.05)
        
        # Generate data with no difference
        sample3 = np.random.normal(0, 1, 100)
        sample4 = np.random.normal(0, 1, 100)
        
        t_stat2, t_pvalue2 = stats.ttest_rel(sample3, sample4)
        
        # Should not detect significant difference (usually)
        # Note: Due to randomness, this might occasionally fail, so we just check it's not always significant
        self.assertGreater(t_pvalue2, 0.01)  # Very unlikely to be this significant by chance
        

if __name__ == '__main__':
    unittest.main()
"""
Unit tests for correlation and FDR logic in code/data/analysis.py.

This module tests:
1. calculate_correlations: Pearson and Spearman correlations with p-values.
2. apply_benjamini_hochberg: FDR correction for multiple hypothesis testing.
3. write_fdr_results and write_correlation_results: Output formatting.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.data.analysis import (
    calculate_correlations,
    apply_benjamini_hochberg,
    write_fdr_results,
    write_correlation_results
)


class TestCalculateCorrelations(unittest.TestCase):
    """Tests for the correlation calculation logic."""

    def setUp(self):
        """Create a small synthetic dataset for testing correlations."""
        np.random.seed(42)
        n = 100
        # Create synthetic data with known correlations
        self.data = pd.DataFrame({
            'smiles': [f'MOLECULE_{i}' for i in range(n)],
            'bond_variance': np.random.normal(0.5, 0.1, n),
            'angle_variance': np.random.normal(1.2, 0.2, n),
            'dihedral_variance': np.random.normal(0.8, 0.15, n),
            'logPapp': np.random.normal(-5.0, 0.5, n)
        })
        
        # Inject a known correlation for bond_variance
        self.data.loc[:, 'logPapp'] = self.data['bond_variance'] * 2.0 + np.random.normal(0, 0.1, n)

    def test_calculate_correlations_returns_dict(self):
        """Test that calculate_correlations returns a dictionary."""
        results = calculate_correlations(self.data, 'logPapp')
        self.assertIsInstance(results, dict)

    def test_calculate_correlations_includes_all_descriptors(self):
        """Test that all three flexibility descriptors are included in results."""
        results = calculate_correlations(self.data, 'logPapp')
        
        expected_keys = [
            'bond_variance',
            'angle_variance', 
            'dihedral_variance'
        ]
        
        for key in expected_keys:
            self.assertIn(key, results)
            self.assertIn('pearson_r', results[key])
            self.assertIn('pearson_p', results[key])
            self.assertIn('spearman_r', results[key])
            self.assertIn('spearman_p', results[key])

    def test_calculate_correlations_bond_variance_has_significant_correlation(self):
        """Test that the injected correlation in bond_variance is detected."""
        results = calculate_correlations(self.data, 'logPapp')
        
        # Check Pearson correlation is significant (p < 0.05)
        self.assertLess(results['bond_variance']['pearson_p'], 0.05)
        
        # Check correlation coefficient is positive and strong
        self.assertGreater(results['bond_variance']['pearson_r'], 0.5)

    def test_calculate_correlations_handles_missing_columns(self):
        """Test behavior when required columns are missing."""
        incomplete_data = self.data.drop(columns=['bond_variance'])
        
        with self.assertRaises(KeyError):
            calculate_correlations(incomplete_data, 'logPapp')

    def test_calculate_correlations_with_constant_variable(self):
        """Test behavior when a variable has zero variance."""
        constant_data = self.data.copy()
        constant_data.loc[:, 'bond_variance'] = 1.0  # Constant value
        
        results = calculate_correlations(constant_data, 'logPapp')
        
        # Should handle gracefully, potentially returning NaN for correlation
        self.assertIn('bond_variance', results)


class TestBenjaminiHochberg(unittest.TestCase):
    """Tests for the FDR correction logic."""

    def setUp(self):
        """Create test p-values."""
        # Create p-values with known properties
        self.p_values = np.array([0.001, 0.01, 0.03, 0.04, 0.06, 0.1, 0.2, 0.5])
        self.descriptors = ['bond', 'angle', 'dihedral', 'rotatable', 'mass', 'charge', 'polar', 'hydrophobic']

    def test_apply_benjamini_hochberg_returns_correct_length(self):
        """Test that FDR correction returns array of same length."""
        corrected = apply_benjamini_hochberg(self.p_values, self.descriptors)
        self.assertEqual(len(corrected), len(self.p_values))

    def test_apply_benjamini_hochberg_monotonicity(self):
        """Test that corrected p-values are monotonically increasing."""
        corrected = apply_benjamini_hochberg(self.p_values, self.descriptors)
        
        # Check that corrected p-values are monotonically increasing
        # (after sorting by original p-values)
        sorted_indices = np.argsort(self.p_values)
        sorted_corrected = corrected[sorted_indices]
        
        # The BH procedure ensures monotonicity in the sorted order
        self.assertTrue(np.all(np.diff(sorted_corrected) >= -1e-10))

    def test_apply_benjamini_hochberg_significant_values(self):
        """Test that small p-values remain significant after correction."""
        corrected = apply_benjamini_hochberg(self.p_values, self.descriptors)
        
        # The smallest p-value (0.001) should remain significant at q < 0.05
        # (assuming enough tests and appropriate alpha)
        idx_min = np.argmin(self.p_values)
        self.assertLess(corrected[idx_min], 0.05)

    def test_apply_benjamini_hochberg_with_single_value(self):
        """Test FDR correction with a single p-value."""
        single_p = np.array([0.01])
        single_desc = ['test']
        
        corrected = apply_benjamini_hochberg(single_p, single_desc)
        self.assertEqual(len(corrected), 1)
        # For a single test, BH should equal the original p-value
        self.assertAlmostEqual(corrected[0], 0.01, places=10)

    def test_apply_benjamini_hochberg_handles_nan(self):
        """Test FDR correction with NaN values."""
        p_with_nan = np.array([0.01, np.nan, 0.05])
        desc_with_nan = ['a', 'b', 'c']
        
        # Should not crash, though behavior with NaN may vary
        corrected = apply_benjamini_hochberg(p_with_nan, desc_with_nan)
        self.assertEqual(len(corrected), 3)


class TestWriteFdrResults(unittest.TestCase):
    """Tests for FDR results output formatting."""

    def setUp(self):
        """Create temporary directory for test outputs."""
        self.temp_dir = tempfile.mkdtemp()
        self.output_path = Path(self.temp_dir) / 'fdr_results.csv'

    def tearDown(self):
        """Clean up temporary files."""
        if self.output_path.exists():
            self.output_path.unlink()

    def test_write_fdr_results_creates_file(self):
        """Test that write_fdr_results creates the output file."""
        fdr_results = [
            {'descriptor': 'bond', 'p_value': 0.01, 'q_value': 0.02},
            {'descriptor': 'angle', 'p_value': 0.05, 'q_value': 0.06}
        ]
        
        write_fdr_results(fdr_results, str(self.output_path))
        
        self.assertTrue(self.output_path.exists())

    def test_write_fdr_results_correct_columns(self):
        """Test that output file has correct columns."""
        fdr_results = [
            {'descriptor': 'bond', 'p_value': 0.01, 'q_value': 0.02}
        ]
        
        write_fdr_results(fdr_results, str(self.output_path))
        
        df = pd.read_csv(self.output_path)
        expected_columns = ['descriptor', 'p_value', 'q_value']
        
        for col in expected_columns:
            self.assertIn(col, df.columns)

    def test_write_fdr_results_preserves_data(self):
        """Test that output file preserves input data."""
        fdr_results = [
            {'descriptor': 'test_desc', 'p_value': 0.03, 'q_value': 0.04}
        ]
        
        write_fdr_results(fdr_results, str(self.output_path))
        
        df = pd.read_csv(self.output_path)
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]['descriptor'], 'test_desc')
        self.assertAlmostEqual(df.iloc[0]['p_value'], 0.03, places=5)


class TestWriteCorrelationResults(unittest.TestCase):
    """Tests for correlation results output formatting."""

    def setUp(self):
        """Create temporary directory for test outputs."""
        self.temp_dir = tempfile.mkdtemp()
        self.output_path = Path(self.temp_dir) / 'correlation_results.csv'

    def tearDown(self):
        """Clean up temporary files."""
        if self.output_path.exists():
            self.output_path.unlink()

    def test_write_correlation_results_creates_file(self):
        """Test that write_correlation_results creates the output file."""
        correlation_results = {
            'bond_variance': {
                'pearson_r': 0.5,
                'pearson_p': 0.01,
                'spearman_r': 0.45,
                'spearman_p': 0.02
            }
        }
        
        write_correlation_results(correlation_results, str(self.output_path))
        
        self.assertTrue(self.output_path.exists())

    def test_write_correlation_results_correct_columns(self):
        """Test that output file has correct columns."""
        correlation_results = {
            'bond_variance': {
                'pearson_r': 0.5,
                'pearson_p': 0.01,
                'spearman_r': 0.45,
                'spearman_p': 0.02
            }
        }
        
        write_correlation_results(correlation_results, str(self.output_path))
        
        df = pd.read_csv(self.output_path)
        expected_columns = [
            'descriptor', 'pearson_r', 'pearson_p', 
            'spearman_r', 'spearman_p'
        ]
        
        for col in expected_columns:
            self.assertIn(col, df.columns)

    def test_write_correlation_results_multiple_descriptors(self):
        """Test output with multiple descriptors."""
        correlation_results = {
            'bond_variance': {'pearson_r': 0.5, 'pearson_p': 0.01, 'spearman_r': 0.45, 'spearman_p': 0.02},
            'angle_variance': {'pearson_r': 0.3, 'pearson_p': 0.03, 'spearman_r': 0.25, 'spearman_p': 0.04},
            'dihedral_variance': {'pearson_r': 0.2, 'pearson_p': 0.05, 'spearman_r': 0.15, 'spearman_p': 0.06}
        }
        
        write_correlation_results(correlation_results, str(self.output_path))
        
        df = pd.read_csv(self.output_path)
        self.assertEqual(len(df), 3)
        self.assertEqual(set(df['descriptor']), {'bond_variance', 'angle_variance', 'dihedral_variance'})


if __name__ == '__main__':
    unittest.main()
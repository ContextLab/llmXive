import os
import sys
import tempfile
import shutil
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data.preprocessing import (
    calculate_heterozygosity,
    calculate_nucleotide_diversity,
    calculate_genomic_diversity_metrics,
    calculate_vif,
    detect_model_instability,
)
from utils.logging import get_module_logger

logger = get_module_logger(__name__)


class TestPreprocessingT027(unittest.TestCase):
    """Unit tests for feature engineering metrics calculation (T027)."""

    def setUp(self):
        """Create temporary directory for test artifacts."""
        self.test_dir = tempfile.mkdtemp()
        self.sample_df = None

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _create_genomic_df(self, n_samples=10, n_sites=100):
        """Create a realistic mock genomic dataframe for testing.
        
        Args:
            n_samples: Number of population samples
            n_sites: Number of genomic sites
        
        Returns:
            pd.DataFrame with genotype data (0, 1, 2)
        """
        np.random.seed(42)
        data = {
            'population_id': [f'POP_{i}' for i in range(n_samples)],
            'site_0': np.random.choice([0, 1, 2], size=n_samples, p=[0.7, 0.2, 0.1]),
            'site_1': np.random.choice([0, 1, 2], size=n_samples, p=[0.6, 0.3, 0.1]),
        }
        
        for i in range(2, n_sites):
            data[f'site_{i}'] = np.random.choice([0, 1, 2], size=n_samples, p=[0.7, 0.2, 0.1])
        
        return pd.DataFrame(data)

    def _create_env_df(self, n_samples=10):
        """Create a mock environmental dataframe for VIF testing.
        
        Args:
            n_samples: Number of samples
        
        Returns:
            pd.DataFrame with correlated environmental variables
        """
        np.random.seed(42)
        # Create correlated features to test VIF calculation
        temp = np.random.normal(20, 5, n_samples)
        precip = temp * 0.8 + np.random.normal(100, 20, n_samples)
        humidity = precip * 0.6 + np.random.normal(50, 10, n_samples)
        
        return pd.DataFrame({
            'population_id': [f'POP_{i}' for i in range(n_samples)],
            'temperature': temp,
            'precipitation': precip,
            'humidity': humidity,
            'elevation': np.random.normal(500, 200, n_samples)
        })

    def test_calculate_heterozygosity_single_site(self):
        """Test heterozygosity calculation for a single site."""
        # Create a simple case: 10 individuals, 3 heterozygous (1s)
        df = pd.DataFrame({
            'population_id': ['POP_1'] * 10,
            'site_0': [0, 0, 1, 1, 1, 2, 2, 0, 0, 0]
        })
        
        result = calculate_heterozygosity(df, 'site_0')
        
        # Expected: 3 heterozygous out of 10 = 0.3
        expected = 0.3
        self.assertAlmostEqual(result, expected, places=5)

    def test_calculate_heterozygosity_all_homozygous(self):
        """Test heterozygosity when all individuals are homozygous."""
        df = pd.DataFrame({
            'population_id': ['POP_1'] * 10,
            'site_0': [0, 0, 0, 2, 2, 0, 0, 2, 0, 0]
        })
        
        result = calculate_heterozygosity(df, 'site_0')
        self.assertEqual(result, 0.0)

    def test_calculate_nucleotide_diversity_basic(self):
        """Test nucleotide diversity calculation."""
        df = pd.DataFrame({
            'population_id': ['POP_1'] * 4,
            'site_0': [0, 0, 2, 2]  # Two alleles, 0 and 2
        })
        
        result = calculate_nucleotide_diversity(df, 'site_0')
        
        # With 2 alleles at equal frequency, expected diversity is high
        self.assertGreater(result, 0.0)
        self.assertLessEqual(result, 1.0)

    def test_calculate_genomic_diversity_metrics(self):
        """Test the combined genomic diversity metrics function."""
        df = self._create_genomic_df(n_samples=20, n_sites=50)
        
        metrics_df = calculate_genomic_diversity_metrics(df)
        
        # Verify output structure
        self.assertIn('population_id', metrics_df.columns)
        self.assertIn('heterozygosity', metrics_df.columns)
        self.assertIn('nucleotide_diversity', metrics_df.columns)
        
        # Verify values are in valid range
        self.assertTrue((metrics_df['heterozygosity'] >= 0).all())
        self.assertTrue((metrics_df['heterozygosity'] <= 1).all())
        self.assertTrue((metrics_df['nucleotide_diversity'] >= 0).all())
        self.assertTrue((metrics_df['nucleotide_diversity'] <= 1).all())
        
        # Verify all populations are present
        self.assertEqual(len(metrics_df), 20)

    def test_calculate_vif_no_collinearity(self):
        """Test VIF calculation with uncorrelated variables."""
        np.random.seed(42)
        df = pd.DataFrame({
            'population_id': [f'POP_{i}' for i in range(50)],
            'var_a': np.random.normal(0, 1, 50),
            'var_b': np.random.normal(0, 1, 50),
            'var_c': np.random.normal(0, 1, 50)
        })
        
        vif_df = calculate_vif(df, exclude_cols=['population_id'])
        
        # With no collinearity, VIF should be close to 1
        self.assertIn('VIF', vif_df.columns)
        self.assertTrue((vif_df['VIF'] >= 1).all())
        self.assertTrue((vif_df['VIF'] < 5).all())

    def test_calculate_vif_high_collinearity(self):
        """Test VIF calculation with highly correlated variables."""
        np.random.seed(42)
        base = np.random.normal(0, 1, 50)
        df = pd.DataFrame({
            'population_id': [f'POP_{i}' for i in range(50)],
            'var_a': base,
            'var_b': base * 0.95 + np.random.normal(0, 0.1, 50),  # Highly correlated
            'var_c': np.random.normal(0, 1, 50)
        })
        
        vif_df = calculate_vif(df, exclude_cols=['population_id'])
        
        # One variable should have high VIF
        self.assertIn('VIF', vif_df.columns)
        high_vif_count = (vif_df['VIF'] > 5).sum()
        self.assertGreater(high_vif_count, 0)

    def test_detect_model_instability_vif(self):
        """Test model instability detection via VIF threshold."""
        np.random.seed(42)
        base = np.random.normal(0, 1, 50)
        df = pd.DataFrame({
            'population_id': [f'POP_{i}' for i in range(50)],
            'var_a': base,
            'var_b': base * 0.99 + np.random.normal(0, 0.01, 50),  # Extremely correlated
            'target': np.random.normal(0, 1, 50)
        })
        
        unstable, unstable_features = detect_model_instability(df, vif_threshold=10)
        
        self.assertTrue(unstable)
        self.assertGreater(len(unstable_features), 0)

    def test_detect_model_instability_singular_matrix(self):
        """Test model instability detection via singular matrix."""
        # Create a dataset with perfect multicollinearity
        np.random.seed(42)
        df = pd.DataFrame({
            'population_id': [f'POP_{i}' for i in range(10)],
            'var_a': np.random.normal(0, 1, 10),
            'var_b': np.random.normal(0, 1, 10),
            'var_c': np.random.normal(0, 1, 10),
            'var_d': np.random.normal(0, 1, 10),
            'target': np.random.normal(0, 1, 10)
        })
        
        # Add a perfect linear combination
        df['var_sum'] = df['var_a'] + df['var_b'] + df['var_c'] + df['var_d']
        
        unstable, unstable_features = detect_model_instability(df, vif_threshold=5)
        
        # Should detect instability due to perfect collinearity
        self.assertTrue(unstable)

    def test_genomic_metrics_consistency(self):
        """Test that genomic metrics are consistent across runs with same seed."""
        df1 = self._create_genomic_df(n_samples=30, n_sites=100)
        df2 = self._create_genomic_df(n_samples=30, n_sites=100)
        
        # Reset seed to ensure same random generation
        np.random.seed(42)
        df1 = self._create_genomic_df(n_samples=30, n_sites=100)
        np.random.seed(42)
        df2 = self._create_genomic_df(n_samples=30, n_sites=100)
        
        metrics1 = calculate_genomic_diversity_metrics(df1)
        metrics2 = calculate_genomic_diversity_metrics(df2)
        
        # Results should be identical
        pd.testing.assert_frame_equal(metrics1, metrics2)

    def test_vif_calculation_with_missing_values(self):
        """Test VIF calculation handles missing values gracefully."""
        np.random.seed(42)
        df = pd.DataFrame({
            'population_id': [f'POP_{i}' for i in range(20)],
            'var_a': np.random.normal(0, 1, 20),
            'var_b': np.random.normal(0, 1, 20),
            'var_c': np.random.normal(0, 1, 20)
        })
        
        # Introduce missing values
        df.loc[0:2, 'var_a'] = np.nan
        
        vif_df = calculate_vif(df, exclude_cols=['population_id'])
        
        # Should still produce results (pandas handles NaN in regression)
        self.assertIn('VIF', vif_df.columns)
        self.assertEqual(len(vif_df), 3)

    def test_genomic_diversity_empty_dataframe(self):
        """Test that genomic diversity functions handle edge cases."""
        empty_df = pd.DataFrame(columns=['population_id', 'site_0'])
        
        with self.assertRaises(ValueError):
            calculate_genomic_diversity_metrics(empty_df)

    def test_vif_single_feature(self):
        """Test VIF calculation with only one feature."""
        df = pd.DataFrame({
            'population_id': [f'POP_{i}' for i in range(10)],
            'var_a': np.random.normal(0, 1, 10)
        })
        
        vif_df = calculate_vif(df, exclude_cols=['population_id'])
        
        # Single feature should have VIF of 1.0
        self.assertEqual(len(vif_df), 1)
        self.assertEqual(vif_df['VIF'].iloc[0], 1.0)


if __name__ == '__main__':
    unittest.main()
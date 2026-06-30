import os
import sys
import tempfile
import shutil
import unittest
from pathlib import Path
import pandas as pd
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.preprocessing import (
    aggregate_to_population_level,
    calculate_vif,
    calculate_genomic_diversity_metrics
)
from utils.logging import configure_root_logger

configure_root_logger()

class TestPreprocessingT020(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_data_path = Path(self.temp_dir) / "test_data.csv"
        
        # Create a sample dataset with multiple populations and predictors
        np.random.seed(42)
        n_samples = 100
        n_populations = 5
        
        data = {
            'population_id': [f'POP_{i % n_populations}' for i in range(n_samples)],
            'env_temp': np.random.normal(20, 5, n_samples),
            'env_precip': np.random.normal(100, 20, n_samples),
            'env_ph': np.random.normal(6.5, 0.5, n_samples),
            'compound_conc': np.random.normal(50, 10, n_samples),
            'genotype_1': np.random.choice([0, 1, 2], n_samples),
            'genotype_2': np.random.choice([0, 1, 2], n_samples),
        }
        
        self.df = pd.DataFrame(data)
        self.df.to_csv(self.test_data_path, index=False)
    
    def tearDown(self):
        """Clean up temporary files."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_aggregate_to_population_level(self):
        """Test FR-009: Aggregate all data to population level."""
        df = self.df.copy()
        
        # Aggregate
        aggregated = aggregate_to_population_level(df, population_col='population_id')
        
        # Assertions
        self.assertEqual(len(aggregated), 5)  # 5 unique populations
        self.assertIn('population_id', aggregated.columns)
        self.assertIn('env_temp', aggregated.columns)
        self.assertIn('env_precip', aggregated.columns)
        self.assertIn('compound_conc', aggregated.columns)
        
        # Check that values are means (not sums)
        original_sum = df.groupby('population_id')['env_temp'].mean()
        aggregated_sum = aggregated.set_index('population_id')['env_temp']
        pd.testing.assert_series_equal(original_sum, aggregated_sum, check_names=False)
    
    def test_aggregate_empty_dataframe(self):
        """Test aggregation with empty DataFrame."""
        empty_df = pd.DataFrame()
        result = aggregate_to_population_level(empty_df, population_col='population_id')
        self.assertTrue(result.empty)
    
    def test_aggregate_with_missing_values(self):
        """Test aggregation handles missing values correctly."""
        df = self.df.copy()
        df.loc[0, 'env_temp'] = np.nan
        
        aggregated = aggregate_to_population_level(df, population_col='population_id')
        
        # Should still have 5 populations
        self.assertEqual(len(aggregated), 5)
        # Mean should handle NaNs (default behavior)
        self.assertFalse(aggregated['env_temp'].isna().any())
    
    def test_calculate_vif_basic(self):
        """Test VIF calculation with basic data."""
        # Create data with some correlation
        np.random.seed(42)
        n = 50
        df = pd.DataFrame({
            'x1': np.random.normal(0, 1, n),
            'x2': np.random.normal(0, 1, n),
            'x3': np.random.normal(0, 1, n),
        })
        
        # Add some correlation between x1 and x2
        df['x2'] = df['x1'] * 0.5 + np.random.normal(0, 0.5, n)
        
        vif_result = calculate_vif(df, exclude_cols=[])
        
        # Should have 3 features
        self.assertEqual(len(vif_result), 3)
        self.assertIn('feature', vif_result.columns)
        self.assertIn('vif', vif_result.columns)
        
        # All VIFs should be non-negative
        self.assertTrue((vif_result['vif'] >= 0).all())
    
    def test_calculate_vif_high_collinearity(self):
        """Test VIF detection of high collinearity (VIF > 5)."""
        # Create data with high collinearity
        np.random.seed(42)
        n = 50
        df = pd.DataFrame({
            'x1': np.random.normal(0, 1, n),
            'x2': np.random.normal(0, 1, n),
        })
        
        # Create highly correlated feature
        df['x3'] = df['x1'] * 0.95 + np.random.normal(0, 0.01, n)
        
        vif_result = calculate_vif(df, exclude_cols=[])
        
        # Find VIF for x3
        x3_vif = vif_result[vif_result['feature'] == 'x3']['vif'].values[0]
        
        # VIF should be > 5 for highly correlated feature
        self.assertGreater(x3_vif, 5.0)
    
    def test_calculate_vif_empty(self):
        """Test VIF calculation with empty DataFrame."""
        empty_df = pd.DataFrame()
        result = calculate_vif(empty_df)
        self.assertTrue(result.empty)
    
    def test_calculate_vif_exclude_cols(self):
        """Test VIF calculation excludes specified columns."""
        df = pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'x1': [1.0, 2.0, 3.0, 4.0, 5.0],
            'x2': [2.0, 3.0, 4.0, 5.0, 6.0],
        })
        
        vif_result = calculate_vif(df, exclude_cols=['id'])
        
        # 'id' should not be in results
        self.assertNotIn('id', vif_result['feature'].values)
        self.assertEqual(len(vif_result), 2)  # Only x1 and x2
    
    def test_integration_aggregate_and_vif(self):
        """Integration test: Aggregate then calculate VIF."""
        df = self.df.copy()
        
        # Step 1: Aggregate to population level
        aggregated = aggregate_to_population_level(df, population_col='population_id')
        
        # Step 2: Calculate VIF on aggregated data
        vif_result = calculate_vif(aggregated, exclude_cols=['population_id'])
        
        # Verify VIF calculation ran
        self.assertFalse(vif_result.empty)
        self.assertIn('feature', vif_result.columns)
        self.assertIn('vif', vif_result.columns)

if __name__ == '__main__':
    unittest.main()

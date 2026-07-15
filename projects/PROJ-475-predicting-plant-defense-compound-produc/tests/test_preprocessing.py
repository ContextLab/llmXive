"""
Unit tests for preprocessing module (T027, T020).
"""
import os
import sys
import tempfile
import shutil
import unittest
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.preprocessing import (
    handle_missing_genotypes,
    handle_missing_env_metadata,
    aggregate_to_population_level,
    calculate_vif
)

class TestPreprocessingT027(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create necessary directories
        Path("data/processed").mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_handle_missing_genotypes_exclusion(self):
        """Test that rows with >20% missing genotypes are excluded."""
        # Create a dataframe with missing values
        data = {
            'population_id': [1, 2, 3, 4],
            'genotype_A': [1.0, 2.0, np.nan, 4.0], # 0% missing
            'genotype_B': [1.0, np.nan, np.nan, 4.0], # 50% missing for row 3
            'genotype_C': [1.0, 2.0, np.nan, 4.0], # 0% missing for row 3 (1/3 = 33% > 20%)
            'compound_value': [10, 20, 30, 40]
        }
        df = pd.DataFrame(data)
        
        # Row 3 has 2 missing out of 3 genotypes (66% > 20%) -> Excluded
        # Row 2 has 1 missing out of 3 (33% > 20%) -> Excluded
        # Wait, Row 2: genotype_B is nan. 1/3 = 33%. Excluded.
        # Row 3: genotype_B and C are nan. 2/3 = 66%. Excluded.
        # Row 1: 0%. Kept.
        # Row 4: 0%. Kept.
        
        result = handle_missing_genotypes(df)
        
        self.assertIn('population_id', result.columns)
        # Check that excluded populations are gone
        self.assertNotIn(2, result['population_id'].values)
        self.assertNotIn(3, result['population_id'].values)
        self.assertIn(1, result['population_id'].values)
        self.assertIn(4, result['population_id'].values)

    def test_handle_missing_genotypes_imputation(self):
        """Test that remaining missing values are imputed with mean."""
        data = {
            'population_id': [1, 2, 3],
            'genotype_A': [1.0, 2.0, 3.0],
            'genotype_B': [1.0, np.nan, 3.0], # 1 missing (33%) -> Excluded?
            # Let's make a case where it's NOT excluded but has missing
            # Need < 20% missing. 1 missing out of 5 columns = 20%.
            # Let's add more columns.
            'genotype_C': [1.0, 2.0, 3.0],
            'genotype_D': [1.0, 2.0, 3.0],
            'genotype_E': [1.0, 2.0, 3.0],
            'compound_value': [10, 20, 30]
        }
        df = pd.DataFrame(data)
        # Row 2: 1 missing out of 5 = 20%. The condition is > 20%, so 20% is kept.
        # Then it should be imputed.
        
        result = handle_missing_genotypes(df)
        
        # Row 2 should be present
        self.assertIn(2, result['population_id'].values)
        # genotype_B for row 2 should be imputed (mean of 1, 3 = 2.0)
        row_2 = result[result['population_id'] == 2]
        self.assertAlmostEqual(row_2['genotype_B'].values[0], 2.0, places=5)

    def test_calculate_vif(self):
        """Test VIF calculation and output file creation."""
        # Create a dataset with some collinearity
        np.random.seed(42)
        n = 50
        data = {
            'population_id': range(n),
            'feature_A': np.random.rand(n),
            'feature_B': np.random.rand(n),
            'feature_C': np.random.rand(n),
            'compound_value': np.random.rand(n)
        }
        df = pd.DataFrame(data)
        
        # Ensure output dir exists
        Path("data/processed").mkdir(exist_ok=True)
        
        vif_df = calculate_vif(df)
        
        # Check that VIF dataframe is returned
        self.assertIsInstance(vif_df, pd.DataFrame)
        self.assertIn('feature', vif_df.columns)
        self.assertIn('vif', vif_df.columns)
        
        # Check that file was created
        vif_path = Path("data/processed/features_vif.csv")
        self.assertTrue(vif_path.exists())
        
        # Check file content
        saved_vif = pd.read_csv(vif_path)
        self.assertEqual(len(saved_vif), len(vif_df))

    def test_aggregate_to_population_level(self):
        """Test aggregation logic."""
        data = {
            'population_id': [1, 1, 2, 2],
            'genotype_A': [1.0, 2.0, 3.0, 4.0],
            'genotype_B': [10.0, 20.0, 30.0, 40.0],
            'compound_value': [100.0, 200.0, 300.0, 400.0]
        }
        df = pd.DataFrame(data)
        
        result = aggregate_to_population_level(df)
        
        # Should have 2 rows (pop 1 and pop 2)
        self.assertEqual(len(result), 2)
        
        # Check aggregation (mean)
        # Pop 1: genotype_A mean = 1.5
        row_1 = result[result['population_id'] == 1]
        self.assertAlmostEqual(row_1['genotype_A'].values[0], 1.5, places=5)

if __name__ == '__main__':
    unittest.main()
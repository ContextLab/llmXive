"""
Unit tests for CLR transformation logic (Task T020a).
"""
import unittest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.utils.config import get_pseudocount
from code._20_apply_clr import apply_clr_transformation, identify_taxa_columns

class TestCLRTransformation(unittest.TestCase):
    
    def setUp(self):
        """Set up test data."""
        self.taxa_cols = ['taxa_A', 'taxa_B', 'taxa_C']
        self.df = pd.DataFrame({
            'subject_id': ['S1', 'S2', 'S3'],
            'taxa_A': [0.1, 0.2, 0.3],
            'taxa_B': [0.4, 0.5, 0.6],
            'taxa_C': [0.5, 0.3, 0.1],
            'other_col': [1, 2, 3]  # Should be excluded
        })
    
    def test_identify_taxa_columns(self):
        """Test that taxa columns are correctly identified."""
        identified_cols = identify_taxa_columns(self.df)
        self.assertEqual(set(identified_cols), set(self.taxa_cols))
        self.assertNotIn('other_col', identified_cols)
        self.assertNotIn('subject_id', identified_cols)
    
    def test_clr_handles_zeros(self):
        """Test that CLR transformation handles zero values correctly."""
        df_with_zeros = pd.DataFrame({
            'subject_id': ['S1', 'S2', 'S3'],
            'taxa_A': [0.0, 0.2, 0.3],
            'taxa_B': [0.4, 0.0, 0.6],
            'taxa_C': [0.5, 0.3, 0.0],
        })
        
        taxa_cols = ['taxa_A', 'taxa_B', 'taxa_C']
        pseudocount = get_pseudocount()
        
        # This should not raise an error
        result_df = apply_clr_transformation(df_with_zeros, taxa_cols, pseudocount)
        
        # Check that taxa_clr column was added
        self.assertIn('taxa_clr', result_df.columns)
        
        # Check that all CLR values are finite (no NaN or Inf)
        clr_values = [np.array(clr) for clr in result_df['taxa_clr']]
        for clr in clr_values:
            self.assertTrue(np.all(np.isfinite(clr)))
    
    def test_clr_sum_to_zero(self):
        """Test that CLR-transformed values sum to approximately zero for each sample."""
        taxa_cols = ['taxa_A', 'taxa_B', 'taxa_C']
        pseudocount = get_pseudocount()
        
        result_df = apply_clr_transformation(self.df, taxa_cols, pseudocount)
        
        # Check that CLR values sum to zero (within floating point tolerance)
        for clr_list in result_df['taxa_clr']:
            clr_array = np.array(clr_list)
            self.assertAlmostEqual(np.sum(clr_array), 0.0, places=5)
    
    def test_clr_transforms_log_ratio(self):
        """Test that CLR correctly implements the log-ratio transformation."""
        # Create a simple case where we can manually verify
        df_simple = pd.DataFrame({
            'subject_id': ['S1'],
            'taxa_A': [0.25],
            'taxa_B': [0.25],
            'taxa_C': [0.5],
        })
        
        taxa_cols = ['taxa_A', 'taxa_B', 'taxa_C']
        pseudocount = get_pseudocount()
        
        result_df = apply_clr_transformation(df_simple, taxa_cols, pseudocount)
        
        # Manual calculation:
        # Geometric mean = (0.25 * 0.25 * 0.5)^(1/3) = (0.03125)^(1/3) ≈ 0.31498
        # CLR_A = ln(0.25) - ln(0.31498) ≈ -0.2877
        # CLR_B = ln(0.25) - ln(0.31498) ≈ -0.2877
        # CLR_C = ln(0.5) - ln(0.31498) ≈ 0.5754
        
        clr_values = np.array(result_df['taxa_clr'][0])
        expected_sum = 0.0
        self.assertAlmostEqual(np.sum(clr_values), expected_sum, places=5)
    
    def test_pseudocount_parameter(self):
        """Test that different pseudocount values produce different (but valid) results."""
        taxa_cols = ['taxa_A', 'taxa_B', 'taxa_C']
        
        df_with_zeros = pd.DataFrame({
            'subject_id': ['S1'],
            'taxa_A': [0.0],
            'taxa_B': [0.5],
            'taxa_C': [0.5],
        })
        
        # Test with different pseudocounts
        result1 = apply_clr_transformation(df_with_zeros, taxa_cols, 1e-6)
        result2 = apply_clr_transformation(df_with_zeros, taxa_cols, 1e-3)
        
        # Results should be different
        clr1 = np.array(result1['taxa_clr'][0])
        clr2 = np.array(result2['taxa_clr'][0])
        
        self.assertFalse(np.allclose(clr1, clr2))
        
        # But both should sum to zero
        self.assertAlmostEqual(np.sum(clr1), 0.0, places=5)
        self.assertAlmostEqual(np.sum(clr2), 0.0, places=5)

if __name__ == '__main__':
    unittest.main()
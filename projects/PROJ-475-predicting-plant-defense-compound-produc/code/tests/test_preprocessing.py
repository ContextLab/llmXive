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

from data.preprocessing import detect_model_instability, calculate_vif, apply_normalization

class TestPreprocessingT027(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_df = pd.DataFrame({
            'population_id': ['pop1', 'pop2', 'pop3', 'pop4', 'pop5'],
            'feature_a': [1.0, 2.0, 3.0, 4.0, 5.0],
            'feature_b': [2.0, 4.0, 6.0, 8.0, 10.0],  # Perfectly correlated with feature_a
            'feature_c': [1.0, 1.5, 2.0, 2.5, 3.0],
            'target': [10, 20, 30, 40, 50]
        })
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_detect_model_instability_high_vif(self):
        """Test detection of high VIF predictors."""
        # feature_b is perfectly correlated with feature_a, should have high VIF
        cleaned_df, removed_predictors = detect_model_instability(self.test_df, vif_threshold=10.0)
        
        # Should detect and remove feature_b due to high VIF
        self.assertIn('feature_b', removed_predictors)
        self.assertNotIn('feature_b', cleaned_df.columns)
        self.assertIn('feature_a', cleaned_df.columns)
        self.assertIn('feature_c', cleaned_df.columns)
    
    def test_detect_model_instability_no_high_vif(self):
        """Test when no predictors have high VIF."""
        test_df = pd.DataFrame({
            'population_id': ['pop1', 'pop2', 'pop3'],
            'feature_a': [1.0, 2.0, 3.0],
            'feature_b': [3.0, 1.0, 2.0],
            'feature_c': [2.0, 3.0, 1.0],
            'target': [10, 20, 30]
        })
        
        cleaned_df, removed_predictors = detect_model_instability(test_df, vif_threshold=10.0)
        
        # No predictors should be removed
        self.assertEqual(len(removed_predictors), 0)
        self.assertEqual(len(cleaned_df.columns), len(test_df.columns))
    
    def test_calculate_vif_basic(self):
        """Test basic VIF calculation."""
        test_df = pd.DataFrame({
            'feature_a': [1.0, 2.0, 3.0, 4.0, 5.0],
            'feature_b': [2.0, 4.0, 6.0, 8.0, 10.0],
            'feature_c': [1.0, 1.5, 2.0, 2.5, 3.0]
        })
        
        vif_df = calculate_vif(test_df, exclude_cols=[])
        
        self.assertEqual(len(vif_df), 3)
        self.assertIn('variable', vif_df.columns)
        self.assertIn('vif', vif_df.columns)
    
    def test_apply_normalization_global(self):
        """Test global Z-score normalization."""
        test_df = pd.DataFrame({
            'population_id': ['pop1', 'pop2', 'pop3'],
            'feature_a': [10.0, 20.0, 30.0],
            'feature_b': [100.0, 200.0, 300.0]
        })
        
        normalized_df = apply_normalization(test_df, unique_studies_count=1)
        
        # Check that normalization was applied
        self.assertAlmostEqual(normalized_df['feature_a'].mean(), 0.0, places=5)
        self.assertAlmostEqual(normalized_df['feature_a'].std(), 1.0, places=5)
    
    def test_apply_normalization_per_study(self):
        """Test per-study Z-score normalization."""
        test_df = pd.DataFrame({
            'population_id': ['pop1', 'pop2', 'pop3', 'pop4'],
            'source_study': ['study1', 'study1', 'study2', 'study2'],
            'feature_a': [10.0, 20.0, 100.0, 200.0]
        })
        
        normalized_df = apply_normalization(test_df, unique_studies_count=2)
        
        # Check that per-study normalization was applied
        study1_data = normalized_df[normalized_df['source_study'] == 'study1']['feature_a']
        study2_data = normalized_df[normalized_df['source_study'] == 'study2']['feature_a']
        
        self.assertAlmostEqual(study1_data.mean(), 0.0, places=5)
        self.assertAlmostEqual(study2_data.mean(), 0.0, places=5)

if __name__ == '__main__':
    unittest.main()
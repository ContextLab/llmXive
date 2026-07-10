import os
import sys
import tempfile
import shutil
import unittest
from pathlib import Path
import pandas as pd
import numpy as np
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.preprocessing import calculate_vif, detect_model_instability

class TestPreprocessingT026(unittest.TestCase):
    """Tests for T026: Model instability detection and conditional predictor removal."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_vif_calculation_no_collinearity(self):
        """Test VIF calculation when features are independent (VIF should be ~1)."""
        np.random.seed(42)
        n_samples = 100
        n_features = 3
        
        # Create independent features
        df = pd.DataFrame({
            'feature1': np.random.randn(n_samples),
            'feature2': np.random.randn(n_samples),
            'feature3': np.random.randn(n_samples)
        })
        
        vif_values = calculate_vif(df, ['feature1', 'feature2', 'feature3'])
        
        # VIF should be close to 1 for independent features
        for feature, vif in vif_values.items():
            self.assertLess(vif, 5.0, f"VIF for {feature} should be < 5, got {vif}")

    def test_vif_calculation_high_collinearity(self):
        """Test VIF calculation when features are highly correlated (VIF should be > 10)."""
        np.random.seed(42)
        n_samples = 100
        
        # Create highly correlated features
        base = np.random.randn(n_samples)
        df = pd.DataFrame({
            'feature1': base,
            'feature2': base * 0.99 + np.random.randn(n_samples) * 0.01,  # Highly correlated
            'feature3': np.random.randn(n_samples)  # Independent
        })
        
        vif_values = calculate_vif(df, ['feature1', 'feature2', 'feature3'])
        
        # feature1 and feature2 should have high VIF
        self.assertGreater(vif_values['feature1'], 10.0, f"VIF for feature1 should be > 10, got {vif_values['feature1']}")
        self.assertGreater(vif_values['feature2'], 10.0, f"VIF for feature2 should be > 10, got {vif_values['feature2']}")
        # feature3 should have low VIF
        self.assertLess(vif_values['feature3'], 5.0, f"VIF for feature3 should be < 5, got {vif_values['feature3']}")

    def test_detect_model_instability_removal(self):
        """Test that detect_model_instability removes features with VIF > 10."""
        np.random.seed(42)
        n_samples = 100
        
        # Create dataset with one unstable feature
        base = np.random.randn(n_samples)
        df = pd.DataFrame({
            'stable1': np.random.randn(n_samples),
            'stable2': np.random.randn(n_samples),
            'unstable': base * 0.99 + np.random.randn(n_samples) * 0.01  # Highly correlated with itself in a way that causes instability
        })
        
        # Make unstable feature highly correlated with stable1
        df['unstable'] = df['stable1'] * 0.999 + np.random.randn(n_samples) * 0.001
        
        stable_df, removed_features = detect_model_instability(df, ['stable1', 'stable2', 'unstable'], vif_threshold=10.0)
        
        # Should remove the unstable feature
        self.assertIn('unstable', removed_features, "Unstable feature should be removed")
        self.assertNotIn('unstable', stable_df.columns, "Unstable feature should not be in output")
        self.assertIn('stable1', stable_df.columns, "Stable feature should be retained")
        self.assertIn('stable2', stable_df.columns, "Stable feature should be retained")

    def test_detect_model_instability_no_removal(self):
        """Test that detect_model_instability keeps all features when no instability exists."""
        np.random.seed(42)
        n_samples = 100
        
        # Create independent features
        df = pd.DataFrame({
            'feature1': np.random.randn(n_samples),
            'feature2': np.random.randn(n_samples),
            'feature3': np.random.randn(n_samples)
        })
        
        stable_df, removed_features = detect_model_instability(df, ['feature1', 'feature2', 'feature3'], vif_threshold=10.0)
        
        # Should not remove any features
        self.assertEqual(len(removed_features), 0, "No features should be removed")
        self.assertEqual(len(stable_df.columns), 3, "All features should be retained")

    def test_singularity_detection(self):
        """Test detection of singular matrix (perfect multicollinearity)."""
        n_samples = 100
        
        # Create perfectly collinear features
        base = np.random.randn(n_samples)
        df = pd.DataFrame({
            'feature1': base,
            'feature2': base * 2.0,  # Perfectly correlated
            'feature3': base * 0.5 + 10  # Perfectly correlated
        })
        
        vif_values = calculate_vif(df, ['feature1', 'feature2', 'feature3'])
        
        # At least one feature should have infinite VIF due to singularity
        has_inf = any(pd.isna(vif) or vif == np.inf for vif in vif_values.values)
        self.assertTrue(has_inf, "Singular matrix should result in infinite VIF")

    def test_edge_case_empty_features(self):
        """Test handling of empty feature list."""
        df = pd.DataFrame({'a': [1, 2, 3]})
        stable_df, removed_features = detect_model_instability(df, [], vif_threshold=10.0)
        
        self.assertEqual(len(removed_features), 0)
        self.assertEqual(len(stable_df.columns), 0)

    def test_edge_case_all_unstable(self):
        """Test handling when all features are unstable."""
        n_samples = 100
        base = np.random.randn(n_samples)
        df = pd.DataFrame({
            'f1': base,
            'f2': base * 0.999,
            'f3': base * 0.998
        })
        
        stable_df, removed_features = detect_model_instability(df, ['f1', 'f2', 'f3'], vif_threshold=10.0)
        
        # All features should be removed
        self.assertEqual(len(removed_features), 3)
        # Result should have no feature columns from the input list
        for col in ['f1', 'f2', 'f3']:
            self.assertNotIn(col, stable_df.columns)

if __name__ == '__main__':
    unittest.main()
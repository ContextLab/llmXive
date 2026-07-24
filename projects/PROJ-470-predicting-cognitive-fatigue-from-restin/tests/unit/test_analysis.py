import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from collinearity import calculate_vif, run_collinearity_diagnostics, save_collinearity_report

class TestVIFCheck:
    """Tests for VIF calculation and collinearity diagnostics."""

    def test_vif_calculation(self):
        """Test that VIF is calculated correctly for a simple dataset."""
        # Create a dataset with known collinearity
        np.random.seed(42)
        n = 100
        
        # Create features with some collinearity
        x1 = np.random.randn(n)
        x2 = x1 * 0.9 + np.random.randn(n) * 0.1  # Highly correlated with x1
        x3 = np.random.randn(n)  # Independent
        
        df = pd.DataFrame({
            'feature1': x1,
            'feature2': x2,
            'feature3': x3
        })
        
        vif_df = calculate_vif(df)
        
        # Check that VIF values are calculated
        assert len(vif_df) == 3
        assert 'feature' in vif_df.columns
        assert 'vif' in vif_df.columns
        
        # Feature 2 should have higher VIF due to correlation with feature 1
        vif_2 = vif_df[vif_df['feature'] == 'feature2']['vif'].values[0]
        assert vif_2 > 1.0  # VIF > 1 indicates some collinearity

    def test_vif_warning_for_high_values(self):
        """Test that warnings are logged for VIF >= 5."""
        # Create a dataset with very high collinearity
        np.random.seed(42)
        n = 100
        
        x1 = np.random.randn(n)
        x2 = x1 * 0.99 + np.random.randn(n) * 0.01  # Very high correlation
        
        df = pd.DataFrame({
            'feature1': x1,
            'feature2': x2
        })
        
        vif_df, warnings = run_collinearity_diagnostics(df, threshold=5.0)
        
        # Check that warning was generated
        assert len(warnings) >= 1
        assert any("High collinearity" in w for w in warnings)

    def test_save_vif_report(self, tmp_path):
        """Test that VIF report is saved correctly."""
        # Create sample data
        df = pd.DataFrame({
            'feature1': [1, 2, 3, 4, 5],
            'feature2': [2, 4, 6, 8, 10],
            'feature3': [1, 1, 1, 1, 1]
        })
        
        output_path = tmp_path / "vif_report.csv"
        
        vif_df = calculate_vif(df)
        save_collinearity_report(vif_df, str(output_path))
        
        # Check that file was created
        assert output_path.exists()
        
        # Check that file contains expected columns
        saved_df = pd.read_csv(output_path)
        assert 'feature' in saved_df.columns
        assert 'vif' in saved_df.columns
        assert len(saved_df) == 3

    def test_vif_with_missing_data(self):
        """Test that VIF calculation handles missing data gracefully."""
        df = pd.DataFrame({
            'feature1': [1, 2, np.nan, 4, 5],
            'feature2': [2, 4, 6, np.nan, 10],
            'feature3': [1, 1, 1, 1, 1]
        })
        
        # Should not raise an error
        vif_df = calculate_vif(df)
        
        # Should have fewer rows due to NaN handling
        assert len(vif_df) == 3  # Still 3 features, but rows with NaN dropped internally

    def test_vif_threshold_parameter(self):
        """Test that different thresholds produce different warning counts."""
        np.random.seed(42)
        n = 100
        
        x1 = np.random.randn(n)
        x2 = x1 * 0.9 + np.random.randn(n) * 0.1
        
        df = pd.DataFrame({
            'feature1': x1,
            'feature2': x2
        })
        
        # Low threshold should produce more warnings
        _, warnings_low = run_collinearity_diagnostics(df, threshold=2.0)
        
        # High threshold should produce fewer warnings
        _, warnings_high = run_collinearity_diagnostics(df, threshold=10.0)
        
        assert len(warnings_low) >= len(warnings_high)

"""
Unit tests for collinearity diagnostics module.

Tests VIF calculation, flagging logic, and diagnostic pipeline.
"""
import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from modeling.collinearity import (
    calculate_vif,
    flag_high_collinearity,
    run_collinearity_diagnostics
)


class TestCalculateVIF:
    """Tests for VIF calculation function."""
    
    def test_vif_no_collinearity(self):
        """Test VIF calculation with uncorrelated features."""
        # Create data with no correlation
        np.random.seed(42)
        df = pd.DataFrame({
            'feature1': np.random.randn(100),
            'feature2': np.random.randn(100),
            'feature3': np.random.randn(100)
        })
        
        vif_df = calculate_vif(df, ['feature1', 'feature2', 'feature3'])
        
        # VIF should be close to 1.0 for uncorrelated features
        assert all(vif_df['vif'] < 2.0), "VIF should be low for uncorrelated features"
        assert len(vif_df) == 3
        
    def test_vif_high_collinearity(self):
        """Test VIF calculation with highly correlated features."""
        # Create data with high correlation
        np.random.seed(42)
        base = np.random.randn(100)
        df = pd.DataFrame({
            'feature1': base,
            'feature2': base * 2 + np.random.randn(100) * 0.1,  # Highly correlated
            'feature3': np.random.randn(100)  # Uncorrelated
        })
        
        vif_df = calculate_vif(df, ['feature1', 'feature2', 'feature3'])
        
        # feature1 and feature2 should have high VIF
        high_vif_features = vif_df[vif_df['vif'] > 5]['feature'].tolist()
        assert 'feature1' in high_vif_features or 'feature2' in high_vif_features, \
            "Highly correlated features should have high VIF"
        
    def test_vif_single_feature(self):
        """Test VIF with a single feature."""
        df = pd.DataFrame({
            'feature1': np.random.randn(100)
        })
        
        vif_df = calculate_vif(df, ['feature1'])
        
        # VIF should be 1.0 for single feature
        assert vif_df['vif'].iloc[0] == 1.0
        
    def test_vif_zero_variance_raises_error(self):
        """Test that zero variance feature raises error."""
        df = pd.DataFrame({
            'feature1': [1.0] * 100,  # Zero variance
            'feature2': np.random.randn(100)
        })
        
        with pytest.raises(ValueError, match="zero variance"):
            calculate_vif(df, ['feature1', 'feature2'])


class TestFlagHighCollinearity:
    """Tests for flagging high collinearity."""
    
    def test_flag_default_threshold(self):
        """Test flagging with default threshold (5.0)."""
        vif_df = pd.DataFrame({
            'feature': ['f1', 'f2', 'f3', 'f4'],
            'vif': [1.5, 4.9, 5.1, 10.0]
        })
        
        high_vif, flagged_df = flag_high_collinearity(vif_df)
        
        assert high_vif == ['f3', 'f4'], "Should flag f3 and f4"
        assert all(flagged_df['high_collinearity'] == [False, False, True, True])
        
    def test_flag_custom_threshold(self):
        """Test flagging with custom threshold."""
        vif_df = pd.DataFrame({
            'feature': ['f1', 'f2', 'f3'],
            'vif': [2.0, 3.0, 4.0]
        })
        
        high_vif, flagged_df = flag_high_collinearity(vif_df, threshold=3.5)
        
        assert high_vif == ['f3'], "Should only flag f3 with threshold 3.5"
        
    def test_flag_no_high_collinearity(self):
        """Test when no features exceed threshold."""
        vif_df = pd.DataFrame({
            'feature': ['f1', 'f2'],
            'vif': [1.5, 2.5]
        })
        
        high_vif, flagged_df = flag_high_collinearity(vif_df)
        
        assert high_vif == []
        assert all(~flagged_df['high_collinearity'])


class TestRunCollinearityDiagnostics:
    """Tests for full diagnostic pipeline."""
    
    def test_run_diagnostics_on_sample_data(self, tmp_path):
        """Test running diagnostics on sample data."""
        # Create sample data
        np.random.seed(42)
        data = {
            'metabolite_A': np.random.randn(50),
            'metabolite_B': np.random.randn(50),
            'metabolite_C': np.random.randn(50)
        }
        df = pd.DataFrame(data)
        
        # Save to temp file
        input_path = tmp_path / "test_matrix.csv"
        df.to_csv(input_path, index=False)
        
        output_path = tmp_path / "collinearity_test.json"
        
        # Run diagnostics
        results = run_collinearity_diagnostics(
            data_path=str(input_path),
            output_path=str(output_path)
        )
        
        # Verify results structure
        assert 'vif_results' in results
        assert 'high_vif_features' in results
        assert 'summary' in results
        
        # Verify summary
        assert results['summary']['total_features'] == 3
        assert results['summary']['threshold'] == 5.0
        
        # Verify output file was created
        assert output_path.exists()
        
    def test_run_diagnostics_file_not_found(self):
        """Test error handling for missing file."""
        with pytest.raises(FileNotFoundError):
            run_collinearity_diagnostics(data_path="/nonexistent/path.csv")
        
    def test_run_diagnostics_empty_features(self, tmp_path):
        """Test error handling for no features."""
        df = pd.DataFrame({'metadata': ['a', 'b', 'c']})
        input_path = tmp_path / "empty.csv"
        df.to_csv(input_path, index=False)
        
        with pytest.raises(ValueError, match="No features found"):
            run_collinearity_diagnostics(
                data_path=str(input_path),
                feature_columns=['nonexistent']
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

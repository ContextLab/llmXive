import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Import the functions to test
from vif_diagnostic import calculate_vif, select_features_with_elastic_net, run_vif_diagnostic

class TestVIFDiagnostic:
    
    @pytest.fixture
    def sample_data(self):
        """Create a sample dataset with some multicollinearity."""
        np.random.seed(42)
        n_samples = 100
        
        # Create features with some correlation
        x1 = np.random.normal(0, 1, n_samples)
        x2 = x1 * 0.9 + np.random.normal(0, 0.1, n_samples)  # Highly correlated with x1
        x3 = np.random.normal(0, 1, n_samples)
        x4 = np.random.normal(0, 1, n_samples)
        y = x1 + x3 + np.random.normal(0, 0.5, n_samples)
        
        df = pd.DataFrame({
            'feature1': x1,
            'feature2': x2,
            'feature3': x3,
            'feature4': x4,
            'target': y
        })
        return df
    
    @pytest.fixture
    def constant_data(self):
        """Create a dataset with a constant feature."""
        n_samples = 50
        df = pd.DataFrame({
            'const_feature': [5.0] * n_samples,
            'normal_feature': np.random.normal(0, 1, n_samples),
            'target': np.random.normal(0, 1, n_samples)
        })
        return df
    
    def test_calculate_vif_basic(self, sample_data):
        """Test basic VIF calculation."""
        features = ['feature1', 'feature2', 'feature3', 'feature4']
        vif_df = calculate_vif(sample_data, features)
        
        assert len(vif_df) == 4
        assert 'feature' in vif_df.columns
        assert 'vif' in vif_df.columns
        
        # Check that VIF values are calculated
        assert all(vif_df['vif'] >= 1.0)
        
    def test_calculate_vif_high_correlation(self, sample_data):
        """Test that highly correlated features get high VIF."""
        features = ['feature1', 'feature2', 'feature3', 'feature4']
        vif_df = calculate_vif(sample_data, features)
        
        # feature1 and feature2 are highly correlated, so at least one should have high VIF
        high_vif_count = (vif_df['vif'] > 5.0).sum()
        assert high_vif_count >= 1, "Expected at least one feature with VIF > 5.0 due to correlation"
        
    def test_calculate_vif_constant_feature(self, constant_data):
        """Test that constant features get infinite VIF."""
        features = ['const_feature', 'normal_feature']
        vif_df = calculate_vif(constant_data, features)
        
        const_row = vif_df[vif_df['feature'] == 'const_feature']
        assert len(const_row) == 1
        assert const_row.iloc[0]['vif'] == float('inf')
        
    def test_select_features_with_elastic_net(self, sample_data):
        """Test Elastic Net feature selection."""
        X = sample_data[['feature1', 'feature2', 'feature3', 'feature4']]
        y = sample_data['target']
        
        selected = select_features_with_elastic_net(X, y, max_features=3)
        
        assert isinstance(selected, list)
        assert len(selected) <= 3
        assert all(f in X.columns for f in selected)
        
    def test_run_vif_diagnostic_full(self, sample_data):
        """Test the full VIF diagnostic workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.csv"
            
            sample_data.to_csv(input_path, index=False)
            
            success, high_vif_features = run_vif_diagnostic(
                input_path, output_path, target_col='target'
            )
            
            assert success
            assert output_path.exists()
            
            # Check that output file has correct structure
            report_df = pd.read_csv(output_path)
            assert 'feature' in report_df.columns
            assert 'vif' in report_df.columns
            assert 'status' in report_df.columns
            assert 'action' in report_df.columns
            
    def test_run_vif_diagnostic_missing_input(self):
        """Test behavior when input file is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "nonexistent.csv"
            output_path = Path(tmpdir) / "output.csv"
            
            success, high_vif_features = run_vif_diagnostic(
                input_path, output_path
            )
            
            assert not success
            assert len(high_vif_features) == 0
            
    def test_vif_threshold_flagging(self, sample_data):
        """Test that VIF > 5 is correctly flagged."""
        features = ['feature1', 'feature2', 'feature3', 'feature4']
        vif_df = calculate_vif(sample_data, features)
        
        # Manually check the logic
        high_vif = vif_df[vif_df['vif'] > 5.0]
        
        # At least one should be high due to correlation
        assert len(high_vif) >= 1

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

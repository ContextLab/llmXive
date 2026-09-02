"""
Unit tests for collinearity diagnostics (T037).
"""
import os
import sys
import pytest
import pandas as pd
import numpy as np
import tempfile
import shutil
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from collinearity import calculate_vif, run_collinearity_diagnostics, save_collinearity_report, load_analysis_results
from utils.logging import get_logger

class TestVIFCalculation:
    """Tests for VIF calculation logic."""
    
    def test_vif_no_collinearity(self):
        """Test VIF calculation with orthogonal predictors (VIF should be 1)."""
        # Create orthogonal data
        np.random.seed(42)
        n = 100
        X1 = np.random.randn(n)
        X2 = np.random.randn(n)
        # Ensure orthogonality
        X2 = X2 - np.cov(X1, X2)[0, 1] / np.var(X1) * X1
        X2 = X2 / np.std(X2)
        
        data = pd.DataFrame({
            'p1': X1,
            'p2': X2
        })
        
        vif_df = calculate_vif(data, ['p1', 'p2'])
        
        # VIF should be close to 1 for orthogonal variables
        assert all(vif_df['vif'] < 1.1), f"VIF should be ~1 for orthogonal data: {vif_df}"
        
    def test_vif_high_collinearity(self):
        """Test VIF calculation with highly correlated predictors (VIF should be high)."""
        np.random.seed(42)
        n = 100
        X1 = np.random.randn(n)
        X2 = X1 * 0.99 + np.random.randn(n) * 0.1  # Highly correlated
        
        data = pd.DataFrame({
            'p1': X1,
            'p2': X2
        })
        
        vif_df = calculate_vif(data, ['p1', 'p2'])
        
        # VIF should be significantly > 1
        assert all(vif_df['vif'] > 10), f"VIF should be high for correlated data: {vif_df}"
        
    def test_vif_perfect_collinearity(self):
        """Test VIF with perfect collinearity (should handle gracefully or return inf)."""
        np.random.seed(42)
        n = 100
        X1 = np.random.randn(n)
        X2 = X1 * 2.0  # Perfectly correlated
        
        data = pd.DataFrame({
            'p1': X1,
            'p2': X2
        })
        
        vif_df = calculate_vif(data, ['p1', 'p2'])
        
        # At least one VIF should be very high or inf
        assert any(vif_df['vif'] >= 100) or any(np.isinf(vif_df['vif'])), \
            f"Perfect collinearity should result in high VIF: {vif_df}"

class TestCollinearityDiagnostics:
    """Tests for the full diagnostics pipeline."""
    
    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary directory for test data."""
        temp_dir = tempfile.mkdtemp()
        processed_dir = os.path.join(temp_dir, "data", "processed")
        os.makedirs(processed_dir)
        yield processed_dir
        shutil.rmtree(temp_dir)
        
    def test_missing_files_raises_error(self, temp_data_dir):
        """Test that missing input files raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_analysis_results(metrics_dir=temp_data_dir)
            
    def test_integration_with_mock_data(self, temp_data_dir):
        """Test full pipeline with mock data that passes VIF check."""
        # Create mock LZW and PE metrics with low correlation
        np.random.seed(42)
        n = 50
        
        lzc_data = pd.DataFrame({
            'participant_id': [f'P{i}' for i in range(n)],
            'F3': np.random.randn(n),
            'F4': np.random.randn(n),
            'C3': np.random.randn(n),
            'C4': np.random.randn(n)
        })
        
        # Create PE data with low correlation to LZW (orthogonal-ish)
        pe_data = pd.DataFrame({
            'participant_id': [f'P{i}' for i in range(n)],
            'F3': np.random.randn(n) * 0.1 + np.random.randn(n),
            'F4': np.random.randn(n) * 0.1 + np.random.randn(n),
            'C3': np.random.randn(n) * 0.1 + np.random.randn(n),
            'C4': np.random.randn(n) * 0.1 + np.random.randn(n)
        })
        
        lzc_data.to_csv(os.path.join(temp_data_dir, "lzc_metrics.csv"), index=False)
        pe_data.to_csv(os.path.join(temp_data_dir, "pe_metrics.csv"), index=False)
        
        # Run diagnostics
        vif_df, is_valid = run_collinearity_diagnostics()
        
        assert is_valid, "Mock data should pass VIF < 5 check"
        assert all(vif_df['vif'] < 5.0), f"VIF values should be < 5: {vif_df}"
        
        # Check output file creation
        output_path = "data/analysis/vif_diagnostics.csv"
        if os.path.exists(output_path):
            saved_df = pd.read_csv(output_path)
            assert len(saved_df) == len(vif_df)
            assert 'predictor' in saved_df.columns
            assert 'vif' in saved_df.columns

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
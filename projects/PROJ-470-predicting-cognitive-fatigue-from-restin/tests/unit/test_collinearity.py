import pytest
import pandas as pd
import numpy as np
import json
import os
import tempfile
from pathlib import Path

# Import the function to test
from collinearity import calculate_vif, run_collinearity_diagnostics

class TestCalculateVIF:
    def test_vif_low_collinearity(self):
        """Test VIF calculation on uncorrelated data."""
        np.random.seed(42)
        n = 100
        df = pd.DataFrame({
            'feature1': np.random.randn(n),
            'feature2': np.random.randn(n),
            'feature3': np.random.randn(n)
        })
        
        vif_df = calculate_vif(df, ['feature1', 'feature2', 'feature3'])
        
        assert 'feature' in vif_df.columns
        assert 'vif' in vif_df.columns
        assert len(vif_df) == 3
        
        # With uncorrelated data, VIF should be close to 1
        assert all(vif_df['vif'] < 2.0), "VIF should be low for uncorrelated data"

    def test_vif_high_collinearity(self):
        """Test VIF calculation on highly correlated data."""
        np.random.seed(42)
        n = 100
        base = np.random.randn(n)
        df = pd.DataFrame({
            'feature1': base,
            'feature2': base * 2 + np.random.randn(n) * 0.1,  # Highly correlated
            'feature3': np.random.randn(n)
        })
        
        vif_df = calculate_vif(df, ['feature1', 'feature2', 'feature3'])
        
        # feature1 and feature2 should have high VIF
        high_vif_features = vif_df[vif_df['vif'] > 5]['feature'].tolist()
        assert 'feature1' in high_vif_features or 'feature2' in high_vif_features, \
            "At least one of the correlated features should have high VIF"

    def test_vif_constant_column(self):
        """Test VIF handling of constant columns."""
        df = pd.DataFrame({
            'feature1': [1.0] * 100,  # Constant
            'feature2': np.random.randn(100),
            'feature3': np.random.randn(100)
        })
        
        # Should handle constant column gracefully (drop it)
        vif_df = calculate_vif(df, ['feature1', 'feature2', 'feature3'])
        
        # feature1 should be excluded
        assert 'feature1' not in vif_df['feature'].tolist()
        assert len(vif_df) == 2

    def test_vif_insufficient_features(self):
        """Test VIF with less than 2 features."""
        df = pd.DataFrame({
            'feature1': np.random.randn(100)
        })
        
        vif_df = calculate_vif(df, ['feature1'])
        
        assert len(vif_df) == 0

class TestRunCollinearityDiagnostics:
    def test_run_diagnostics_success(self):
        """Test successful run of collinearity diagnostics."""
        # Create temporary files
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mock processed metrics
            lzc_path = Path(tmpdir) / 'lzc_metrics.csv'
            pe_path = Path(tmpdir) / 'pe_metrics.csv'
            report_path = Path(tmpdir) / 'collinearity_report.json'
            
            # Generate mock data
            n = 50
            df_lzc = pd.DataFrame({
                'participant_id': range(n),
                'lzc_fz': np.random.randn(n),
                'lzc_cz': np.random.randn(n)
            })
            df_pe = pd.DataFrame({
                'participant_id': range(n),
                'pe_fz': np.random.randn(n),
                'pe_cz': np.random.randn(n)
            })
            
            df_lzc.to_csv(lzc_path, index=False)
            df_pe.to_csv(pe_path, index=False)
            
            # Create a minimal config
            config_path = Path(tmpdir) / 'config.yaml'
            with open(config_path, 'w') as f:
                f.write("pipeline:\n  random_seed: 42\n")
            
            # Run diagnostics
            result = run_collinearity_diagnostics(
                results_path=Path(tmpdir) / 'nonexistent.json', # Will be ignored if files exist
                config_path=str(config_path),
                vif_threshold=5.0,
                output_path=str(report_path)
            )
            
            # Verify report was created
            assert os.path.exists(report_path)
            with open(report_path, 'r') as f:
                report = json.load(f)
            
            assert 'status' in report
            assert 'vif_results' in report
            assert 'max_vif' in report

    def test_run_diagnostics_failed_threshold(self):
        """Test diagnostics when VIF exceeds threshold."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lzc_path = Path(tmpdir) / 'lzc_metrics.csv'
            pe_path = Path(tmpdir) / 'pe_metrics.csv'
            report_path = Path(tmpdir) / 'collinearity_report.json'
            
            # Create highly correlated data
            n = 50
            base = np.random.randn(n)
            df_lzc = pd.DataFrame({
                'participant_id': range(n),
                'lzc_fz': base,
                'lzc_cz': base * 2 + np.random.randn(n) * 0.1
            })
            df_pe = pd.DataFrame({
                'participant_id': range(n),
                'pe_fz': np.random.randn(n),
                'pe_cz': np.random.randn(n)
            })
            
            df_lzc.to_csv(lzc_path, index=False)
            df_pe.to_csv(pe_path, index=False)
            
            config_path = Path(tmpdir) / 'config.yaml'
            with open(config_path, 'w') as f:
                f.write("pipeline:\n  random_seed: 42\n")
            
            result = run_collinearity_diagnostics(
                results_path=Path(tmpdir) / 'nonexistent.json',
                config_path=str(config_path),
                vif_threshold=2.0, # Low threshold to trigger failure
                output_path=str(report_path)
            )
            
            with open(report_path, 'r') as f:
                report = json.load(f)
            
            assert report['status'] == 'failed'
            assert report['max_vif'] > 2.0

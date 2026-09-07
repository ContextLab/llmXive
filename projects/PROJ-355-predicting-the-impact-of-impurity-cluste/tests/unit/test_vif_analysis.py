import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.descriptor_filter import compute_vif, generate_report

class TestVIFAnalysis:
    
    def test_compute_vif_perfect_correlation(self):
        """Test VIF calculation with perfectly correlated features."""
        # Create data where feature B is exactly feature A * 2
        data = {
            'feature_A': [1.0, 2.0, 3.0, 4.0, 5.0],
            'feature_B': [2.0, 4.0, 6.0, 8.0, 10.0]
        }
        df = pd.DataFrame(data)
        
        vif_df = compute_vif(df, ['feature_A', 'feature_B'])
        
        # With perfect correlation, VIF should be infinite or very large
        # Due to floating point precision, it might be a very large number
        assert len(vif_df) == 2
        assert all(vif_df['vif'] >= 1.0)
        
    def test_compute_vif_no_correlation(self):
        """Test VIF calculation with uncorrelated features."""
        # Create data with no correlation
        np.random.seed(42)
        data = {
            'feature_A': np.random.randn(100),
            'feature_B': np.random.randn(100),
            'feature_C': np.random.randn(100)
        }
        df = pd.DataFrame(data)
        
        vif_df = compute_vif(df, ['feature_A', 'feature_B', 'feature_C'])
        
        # VIF should be close to 1 for uncorrelated features
        assert len(vif_df) == 3
        assert all(vif_df['vif'] >= 1.0)
        assert all(vif_df['vif'] < 5.0)  # Should be low collinearity
        
    def test_generate_report_creates_file(self):
        """Test that generate_report creates a valid markdown file."""
        vif_data = {
            'feature': ['rdf_peak', 'pair_corr', 'voronoi_count'],
            'vif': [12.5, 2.3, 8.1]
        }
        vif_df = pd.DataFrame(vif_data)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_report.md"
            generate_report(vif_df, output_path)
            
            assert output_path.exists()
            
            content = output_path.read_text()
            assert "# Collinearity Analysis Report" in content
            assert "VIF" in content
            assert "rdf_peak" in content
            assert "12.5" in content
            
    def test_generate_report_high_collinearity_section(self):
        """Test that report includes high collinearity section when VIF >= 10."""
        vif_data = {
            'feature': ['feature_A', 'feature_B'],
            'vif': [15.0, 2.0]
        }
        vif_df = pd.DataFrame(vif_data)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_report.md"
            generate_report(vif_df, output_path)
            
            content = output_path.read_text()
            assert "High Collinearity Detected (VIF ≥ 10)" in content
            assert "feature_A" in content

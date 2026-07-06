"""
Unit tests for code/data/descriptor_filter.py
"""
import os
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json

# Mock config for testing if not available, but we assume config is set up by T001/T002
# Since we are running in a test environment, we might need to mock get_project_root
# However, for this task, we focus on the logic of VIF calculation and report generation.

from data.descriptor_filter import compute_vif, generate_report, VIF_THRESHOLD

@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame with some collinearity."""
    # Create data where 'pair_corr' is highly correlated with 'rdf_peak'
    np.random.seed(42)
    n = 50
    rdf = np.random.randn(n)
    pair_corr = rdf * 0.95 + np.random.randn(n) * 0.05 # High correlation
    voronoi = np.random.randn(n)
    
    return pd.DataFrame({
        'rdf_peak': rdf,
        'pair_corr': pair_corr,
        'voronoi_count': voronoi
    })

def test_compute_vif_basic(sample_dataframe):
    """Test that VIF is computed correctly for a standard dataset."""
    features = ['rdf_peak', 'pair_corr', 'voronoi_count']
    vif_df = compute_vif(sample_dataframe, features)
    
    assert isinstance(vif_df, pd.DataFrame)
    assert 'feature' in vif_df.columns
    assert 'vif' in vif_df.columns
    assert len(vif_df) == 3
    
    # Check that VIF values are positive
    assert all(vif_df['vif'] > 0)
    
    # Check that the highly correlated features have higher VIF
    # pair_corr and rdf_peak should have higher VIF than voronoi_count
    # Note: Exact values depend on the random seed and data, but the trend should hold
    rdf_vif = vif_df[vif_df['feature'] == 'rdf_peak']['vif'].values[0]
    pair_vif = vif_df[vif_df['feature'] == 'pair_corr']['vif'].values[0]
    voronoi_vif = vif_df[vif_df['feature'] == 'voronoi_count']['vif'].values[0]
    
    assert rdf_vif > 1.0
    assert pair_vif > 1.0
    # The correlated pair should have significantly higher VIF than the independent one
    assert max(rdf_vif, pair_vif) > voronoi_vif

def test_generate_report_creates_file(sample_dataframe):
    """Test that the report generation creates a markdown file with expected content."""
    features = ['rdf_peak', 'pair_corr', 'voronoi_count']
    vif_df = compute_vif(sample_dataframe, features)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = Path(tmpdir) / "test_report.md"
        generate_report(vif_df, report_path)
        
        assert report_path.exists()
        
        content = report_path.read_text()
        assert "Collinearity Report" in content
        assert "VIF Threshold" in content or str(VIF_THRESHOLD) in content
        assert "Feature" in content and "VIF Score" in content

def test_generate_report_high_vif_detection(sample_dataframe):
    """Test that the report correctly identifies high VIF features."""
    features = ['rdf_peak', 'pair_corr', 'voronoi_count']
    vif_df = compute_vif(sample_dataframe, features)
    
    # Force a high VIF scenario by modifying data if necessary, 
    # but with the seed 42 and correlation 0.95, VIF should be > 10 for the correlated pair.
    # VIF for correlation r is approx 1/(1-r^2). If r=0.95, VIF ~ 1/(1-0.9025) = 1/0.0975 ~ 10.25
    
    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = Path(tmpdir) / "test_report_high_vif.md"
        generate_report(vif_df, report_path)
        
        content = report_path.read_text()
        
        # Check for the high collinearity section if VIF >= 10
        if any(vif_df['vif'] >= VIF_THRESHOLD):
            assert "High Collinearity Detected" in content
            assert "Severe multicollinearity" in content or "High multicollinearity" in content
        else:
            # If VIF < 10, it should say no high collinearity
            assert "No features exceeded the VIF threshold" in content

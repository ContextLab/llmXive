"""
Unit tests for collinearity diagnostics (T022).
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.modeling.collinearity import (
    calculate_vif,
    flag_high_collinearity,
    run_collinearity_diagnostics,
    VIF_THRESHOLD
)

class TestCalculateVIF:
    """Tests for VIF calculation function."""
    
    def test_vif_basic(self):
        """Test VIF calculation with simple data."""
        # Create data with known correlation structure
        np.random.seed(42)
        n = 100
        X = pd.DataFrame({
            'feature1': np.random.randn(n),
            'feature2': np.random.randn(n),
            'feature3': np.random.randn(n)
        })
        
        vif = calculate_vif(X)
        
        # VIF should be calculated for all features
        assert len(vif) == 3
        assert all(vif >= 1.0), "VIF values should be >= 1.0"
        
    def test_vif_high_collinearity(self):
        """Test VIF detects high collinearity."""
        np.random.seed(42)
        n = 100
        base = np.random.randn(n)
        
        X = pd.DataFrame({
            'feature1': base,
            'feature2': base * 2 + np.random.randn(n) * 0.1,  # Highly correlated
            'feature3': np.random.randn(n)  # Independent
        })
        
        vif = calculate_vif(X)
        
        # feature1 and feature2 should have high VIF
        assert vif['feature1'] > 5.0, "Collinear feature should have VIF > 5"
        assert vif['feature2'] > 5.0, "Collinear feature should have VIF > 5"
        
    def test_vif_missing_values_raises(self):
        """Test that VIF calculation raises on missing values."""
        X = pd.DataFrame({
            'feature1': [1.0, 2.0, np.nan, 4.0],
            'feature2': [1.0, 2.0, 3.0, 4.0]
        })
        
        with pytest.raises(ValueError, match="NaN"):
            calculate_vif(X)
            
    def test_vif_constant_feature_raises(self):
        """Test that VIF calculation raises on constant features."""
        X = pd.DataFrame({
            'feature1': [1.0, 1.0, 1.0, 1.0],
            'feature2': [1.0, 2.0, 3.0, 4.0]
        })
        
        with pytest.raises(ValueError, match="zero variance"):
            calculate_vif(X)

class TestFlagHighCollinearity:
    """Tests for collinearity flagging function."""
    
    def test_flag_threshold(self):
        """Test flagging with custom threshold."""
        vif_series = pd.Series({
            'f1': 2.0,
            'f2': 6.0,
            'f3': 8.0,
            'f4': 3.0
        })
        
        flagged = flag_high_collinearity(vif_series, threshold=5.0)
        
        assert len(flagged) == 2
        assert set(flagged['feature']) == {'f2', 'f3'}
        
    def test_flag_no_collinearity(self):
        """Test when no features exceed threshold."""
        vif_series = pd.Series({
            'f1': 2.0,
            'f2': 3.0,
            'f3': 4.0
        })
        
        flagged = flag_high_collinearity(vif_series, threshold=5.0)
        
        assert len(flagged) == 0
        
    def test_flag_all_collinearity(self):
        """Test when all features exceed threshold."""
        vif_series = pd.Series({
            'f1': 6.0,
            'f2': 7.0,
            'f3': 8.0
        })
        
        flagged = flag_high_collinearity(vif_series, threshold=5.0)
        
        assert len(flagged) == 3

class TestRunCollinearityDiagnostics:
    """Tests for full diagnostics pipeline."""
    
    def test_diagnostics_creates_output(self, tmp_path):
        """Test that diagnostics creates output file."""
        np.random.seed(42)
        X = pd.DataFrame({
            'f1': np.random.randn(50),
            'f2': np.random.randn(50),
            'f3': np.random.randn(50)
        })
        
        output_file = tmp_path / "test_diagnostics.json"
        
        results = run_collinearity_diagnostics(X, output_file)
        
        assert output_file.exists()
        assert 'summary' in results
        assert 'vif_values' in results
        assert 'flagged_features' in results
        assert results['summary']['total_features'] == 3
        
    def test_diagnostics_summary_stats(self):
        """Test summary statistics are correct."""
        np.random.seed(42)
        X = pd.DataFrame({
            'f1': np.random.randn(50),
            'f2': np.random.randn(50),
            'f3': np.random.randn(50)
        })
        
        results = run_collinearity_diagnostics(X)
        
        summary = results['summary']
        assert summary['total_features'] == 3
        assert 'max_vif' in summary
        assert 'mean_vif' in summary
        assert summary['threshold'] == VIF_THRESHOLD
        assert 'timestamp' in summary
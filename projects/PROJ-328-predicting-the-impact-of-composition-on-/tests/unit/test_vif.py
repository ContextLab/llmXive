"""
Unit tests for code/features/collinearity.py
"""
import pytest
import pandas as pd
import numpy as np
import tempfile
from pathlib import Path
import sys
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from features.collinearity import calculate_vif, get_collinear_features, save_vif_report


class TestVIF:
    """Tests for VIF calculation and collinearity detection."""

    @pytest.fixture
    def sample_features(self):
        """Create sample feature data with some correlation."""
        np.random.seed(42)
        n = 100
        X1 = np.random.randn(n)
        X2 = X1 * 0.9 + np.random.randn(n) * 0.1  # Highly correlated with X1
        X3 = np.random.randn(n)  # Independent
        
        return pd.DataFrame({
            'X1': X1,
            'X2': X2,
            'X3': X3
        })

    def test_calculate_vif(self, sample_features):
        """Test VIF calculation."""
        vif_values = calculate_vif(sample_features)
        
        # X2 should have high VIF due to correlation with X1
        assert vif_values['X2'] > 5.0
        
        # X3 should have low VIF
        assert vif_values['X3'] < 5.0

    def test_get_collinear_features(self, sample_features):
        """Test detection of collinear features."""
        collinear = get_collinear_features(sample_features, threshold=5.0)
        
        # X2 should be flagged as collinear
        assert 'X2' in collinear

    def test_save_vif_report(self, sample_features, tmp_path):
        """Test saving VIF report to YAML."""
        output_path = tmp_path / "vif_report.yaml"
        
        vif_values = calculate_vif(sample_features)
        collinear = get_collinear_features(sample_features, threshold=5.0)
        
        save_vif_report(vif_values, collinear, str(output_path))
        
        assert output_path.exists()
        
        # Load and verify content
        with open(output_path, 'r') as f:
            report = yaml.safe_load(f)
        
        assert 'predictors' in report
        assert 'collinear_features' in report
        assert len(report['predictors']) == 3

    def test_vif_report_schema(self, sample_features, tmp_path):
        """Test VIF report schema compliance."""
        output_path = tmp_path / "vif_report.yaml"
        
        vif_values = calculate_vif(sample_features)
        collinear = get_collinear_features(sample_features, threshold=5.0)
        
        save_vif_report(vif_values, collinear, str(output_path))
        
        with open(output_path, 'r') as f:
            report = yaml.safe_load(f)
        
        # Check required fields
        assert 'predictors' in report
        for predictor in report['predictors']:
            assert 'name' in predictor
            assert 'vif_score' in predictor
            assert 'is_collinear' in predictor

    def test_highly_collinear_data(self):
        """Test VIF on highly collinear data."""
        np.random.seed(42)
        n = 50
        X = np.random.randn(n)
        # Create highly correlated features
        data = pd.DataFrame({
            'A': X,
            'B': X * 0.99,
            'C': X * 0.98
        })
        
        vif_values = calculate_vif(data)
        
        # All features should have very high VIF
        assert all(v > 100 for v in vif_values.values)

    def test_independent_features(self):
        """Test VIF on independent features."""
        np.random.seed(42)
        n = 100
        data = pd.DataFrame({
            'A': np.random.randn(n),
            'B': np.random.randn(n),
            'C': np.random.randn(n)
        })
        
        vif_values = calculate_vif(data)
        
        # All features should have low VIF (close to 1)
        assert all(1.0 <= v < 5.0 for v in vif_values.values)

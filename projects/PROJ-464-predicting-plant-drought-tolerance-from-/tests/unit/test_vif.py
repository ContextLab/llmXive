import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os
import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from analysis import calculate_vif, generate_vif_report

class TestVIFCalculation:
    def test_calculate_vif_returns_dict(self):
        """Test that calculate_vif returns a dictionary with correct keys."""
        data = {
            'depth': [1.0, 2.0, 3.0, 4.0, 5.0],
            'branching_density': [10.0, 20.0, 30.0, 40.0, 50.0],
            'surface_area': [100.0, 200.0, 300.0, 400.0, 500.0]
        }
        df = pd.DataFrame(data)
        features = ['depth', 'branching_density', 'surface_area']
        
        vif_scores = calculate_vif(df, features)
        
        assert isinstance(vif_scores, dict)
        assert set(vif_scores.keys()) == set(features)
        assert all(isinstance(v, float) for v in vif_scores.values())

    def test_calculate_vif_high_collinearity(self):
        """Test VIF calculation with highly correlated features."""
        # Create data with perfect correlation (VIF should be very high or infinite)
        x = np.linspace(0, 10, 100)
        data = {
            'feature_a': x,
            'feature_b': x * 2 + 0.001, # Highly correlated
            'feature_c': np.random.rand(100) # Independent
        }
        df = pd.DataFrame(data)
        features = ['feature_a', 'feature_b', 'feature_c']
        
        vif_scores = calculate_vif(df, features)
        
        # feature_a and feature_b should have high VIF
        assert vif_scores['feature_a'] > 10 or np.isinf(vif_scores['feature_a'])
        assert vif_scores['feature_b'] > 10 or np.isinf(vif_scores['feature_b'])

    def test_generate_vif_report_creates_file(self, tmp_path):
        """Test that generate_vif_report creates a valid YAML file."""
        vif_scores = {
            'depth': 2.5,
            'branching_density': 6.0,
            'surface_area': 1.2
        }
        output_path = tmp_path / "vif_report.yaml"
        
        generate_vif_report(vif_scores, output_path)
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            report = yaml.safe_load(f)
        
        assert 'vif_scores' in report
        assert report['vif_scores'] == vif_scores
        assert 'high_vif_features' in report
        assert 'branching_density' in report['high_vif_features']
        assert report['status'] == 'warning'

    def test_vif_report_all_low(self, tmp_path):
        """Test report status when all VIFs are low."""
        vif_scores = {
            'depth': 2.0,
            'branching_density': 1.5,
            'surface_area': 1.0
        }
        output_path = tmp_path / "vif_report.yaml"
        
        generate_vif_report(vif_scores, output_path)
        
        with open(output_path, 'r') as f:
            report = yaml.safe_load(f)
        
        assert report['status'] == 'ok'
        assert len(report['high_vif_features']) == 0
"""
Unit tests for VIF computation and collinearity mitigation in src/utils/metrics.py
"""
import os
import sys
import tempfile
import json
import pandas as pd
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from src.utils.metrics import compute_vif, residualize_features, check_and_mitigate_collinearity, update_performance_metrics


class TestVIFComputation:
    def test_vif_perfect_collinearity(self):
        """Test VIF calculation with perfect collinearity (should be high)"""
        df = pd.DataFrame({
            'x1': [1, 2, 3, 4, 5],
            'x2': [2, 4, 6, 8, 10],  # Perfectly correlated with x1
            'x3': [1, 0, 1, 0, 1]
        })
        
        vif_scores = compute_vif(df, ['x1', 'x2', 'x3'])
        
        # x2 should have very high VIF due to perfect correlation with x1
        assert 'x1' in vif_scores
        assert 'x2' in vif_scores
        assert vif_scores['x2'] > 1000  # Should be extremely high
        
    def test_vif_no_collinearity(self):
        """Test VIF calculation with uncorrelated features"""
        np.random.seed(42)
        df = pd.DataFrame({
            'x1': np.random.randn(100),
            'x2': np.random.randn(100),
            'x3': np.random.randn(100)
        })
        
        vif_scores = compute_vif(df, ['x1', 'x2', 'x3'])
        
        # VIFs should be low (close to 1)
        for col in ['x1', 'x2', 'x3']:
            assert vif_scores[col] < 5.0
            
    def test_vif_empty_features(self):
        """Test VIF calculation with empty feature list"""
        df = pd.DataFrame({'x1': [1, 2, 3]})
        vif_scores = compute_vif(df, [])
        assert vif_scores == {}
        
    def test_vif_nan_handling(self):
        """Test that VIF calculation handles NaN values by dropping them"""
        df = pd.DataFrame({
            'x1': [1.0, 2.0, np.nan, 4.0, 5.0],
            'x2': [2.0, 4.0, 6.0, 8.0, 10.0],
        })
        
        # Should not raise an error
        vif_scores = compute_vif(df, ['x1', 'x2'])
        assert len(vif_scores) == 2
        # x2 should still show high VIF (perfect correlation with x1 on valid rows)


class TestResidualization:
    def test_residualize_high_vif(self):
        """Test residualization logic when high VIF is present"""
        # Create data with high collinearity
        x1 = np.linspace(1, 10, 50)
        x2 = x1 * 2 + np.random.normal(0, 0.1, 50) # Highly correlated
        x3 = np.random.randn(50)
        y = x1 + x2 + x3 + np.random.normal(0, 0.1, 50)
        
        df = pd.DataFrame({
            'x1': x1,
            'x2': x2,
            'x3': x3,
            'Tg': y
        })
        
        # Perform residualization
        df_resid, info = residualize_features(df, 'Tg', ['x1', 'x2', 'x3'])
        
        # Check that residualized column exists
        assert 'x1_resid' in df_resid.columns or 'x2_resid' in df_resid.columns
        
    def test_residualize_no_high_vif(self):
        """Test that residualization returns original df if no high VIF"""
        np.random.seed(42)
        df = pd.DataFrame({
            'x1': np.random.randn(50),
            'x2': np.random.randn(50),
            'x3': np.random.randn(50),
            'Tg': np.random.randn(50)
        })
        
        df_resid, info = residualize_features(df, 'Tg', ['x1', 'x2', 'x3'])
        
        # Should be essentially unchanged (ignoring index alignment)
        assert 'x1_resid' not in df_resid.columns


class TestCollinearityMitigation:
    def test_check_and_mitigate_trigger(self, tmp_path):
        """Test that mitigation is triggered when VIF >= 5"""
        # Create a temporary directory for artifacts
        with patch('src.utils.metrics.PERFORMANCE_METRICS_PATH', tmp_path / 'performance_metrics.json'):
            # Create data with high collinearity
            x1 = np.linspace(1, 10, 50)
            x2 = x1 * 2 + np.random.normal(0, 0.1, 50)
            x3 = np.random.randn(50)
            y = x1 + x2 + x3 + np.random.normal(0, 0.1, 50)
            
            df = pd.DataFrame({
                'x1': x1,
                'x2': x2,
                'x3': x3,
                'Tg': y
            })
            
            triggered, strategy = check_and_mitigate_collinearity(df, ['x1', 'x2', 'x3'], 'Tg')
            
            assert triggered is True
            assert strategy == 'residualization'
            
            # Verify metrics file was updated
            metrics_file = tmp_path / 'performance_metrics.json'
            assert metrics_file.exists()
            
            with open(metrics_file, 'r') as f:
                metrics = json.load(f)
            
            assert 'collinearity_mitigation' in metrics
            assert metrics['collinearity_mitigation'] == 'residualization'
            assert 'vif_scores' in metrics

    def test_check_and_mitigate_no_trigger(self, tmp_path):
        """Test that mitigation is NOT triggered when VIF < 5"""
        with patch('src.utils.metrics.PERFORMANCE_METRICS_PATH', tmp_path / 'performance_metrics.json'):
            np.random.seed(42)
            df = pd.DataFrame({
                'x1': np.random.randn(50),
                'x2': np.random.randn(50),
                'x3': np.random.randn(50),
                'Tg': np.random.randn(50)
            })
            
            triggered, strategy = check_and_mitigate_collinearity(df, ['x1', 'x2', 'x3'], 'Tg')
            
            assert triggered is False
            assert strategy == 'none'
            
            metrics_file = tmp_path / 'performance_metrics.json'
            assert metrics_file.exists()
            
            with open(metrics_file, 'r') as f:
                metrics = json.load(f)
            
            assert metrics['collinearity_mitigation'] == 'none_required'


class TestUpdatePerformanceMetrics:
    def test_update_metrics_creates_file(self, tmp_path):
        """Test that update_performance_metrics creates the file if it doesn't exist"""
        metrics_path = tmp_path / 'performance_metrics.json'
        
        with patch('src.utils.metrics.PERFORMANCE_METRICS_PATH', metrics_path):
            update_performance_metrics({'x1': 2.0}, 'none_required')
            
            assert metrics_path.exists()
            
            with open(metrics_path, 'r') as f:
                metrics = json.load(f)
            
            assert metrics['vif_scores']['x1'] == 2.0
            assert metrics['collinearity_mitigation'] == 'none_required'
    
    def test_update_metrics_overwrites_existing(self, tmp_path):
        """Test that update_performance_metrics correctly updates existing metrics"""
        metrics_path = tmp_path / 'performance_metrics.json'
        
        # Create initial file
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        with open(metrics_path, 'w') as f:
            json.dump({'existing_key': 'value'}, f)
        
        with patch('src.utils.metrics.PERFORMANCE_METRICS_PATH', metrics_path):
            update_performance_metrics({'x1': 6.0}, 'residualization')
            
            with open(metrics_path, 'r') as f:
                metrics = json.load(f)
            
            assert metrics['existing_key'] == 'value'
            assert metrics['vif_scores']['x1'] == 6.0
            assert metrics['collinearity_mitigation'] == 'residualization'
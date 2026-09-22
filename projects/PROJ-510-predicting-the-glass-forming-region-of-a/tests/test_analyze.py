"""
Tests for code/analyze.py
"""
import pytest
import pandas as pd
import numpy as np
import os
import sys
import json
import tempfile
import shutil
import pickle

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from analyze import load_model_and_data, check_collinearity, analyze_feature_importance, retrain_stable_model, run_collinearity_and_retrain, run_sensitivity_analysis
from utils import ensure_dir

class TestAnalyze:
    """Test suite for analysis module."""

    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        np.random.seed(42)
        n_samples = 100
        data = {
            'mixing_enthalpy': np.random.randn(n_samples) * 5,
            'atomic_size_mismatch': np.random.randn(n_samples) * 2,
            'electronegativity_variance': np.random.randn(n_samples) * 0.5,
            'critical_cooling_rate': np.random.randn(n_samples) * 50 + 100
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test artifacts."""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path)

    def test_check_collinearity(self, sample_data):
        """Test collinearity detection."""
        feature_cols = ['mixing_enthalpy', 'atomic_size_mismatch', 'electronegativity_variance']
        
        collinearity_report = check_collinearity(sample_data, feature_cols)
        
        assert isinstance(collinearity_report, dict)
        assert 'collinear_pairs' in collinearity_report
        assert 'correlation_matrix' in collinearity_report

    def test_analyze_feature_importance(self, sample_data, temp_dir):
        """Test feature importance analysis."""
        # Train a simple model first
        from sklearn.ensemble import RandomForestRegressor
        
        feature_cols = ['mixing_enthalpy', 'atomic_size_mismatch', 'electronegativity_variance']
        target_col = 'critical_cooling_rate'
        
        X = sample_data[feature_cols]
        y = sample_data[target_col]
        
        model = RandomForestRegressor(random_state=42, n_estimators=10)
        model.fit(X, y)
        
        # Save model
        model_path = os.path.join(temp_dir, 'test_model.pkl')
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        
        # Analyze importance
        importance_report = analyze_feature_importance(model_path, X, y, feature_cols)
        
        assert isinstance(importance_report, dict)
        assert 'feature_importance' in importance_report
        assert 'p_values' in importance_report

    def test_retrain_stable_model(self, sample_data, temp_dir):
        """Test retraining a stable model."""
        from sklearn.ensemble import RandomForestRegressor
        
        feature_cols = ['mixing_enthalpy', 'atomic_size_mismatch', 'electronegativity_variance']
        target_col = 'critical_cooling_rate'
        
        X = sample_data[feature_cols]
        y = sample_data[target_col]
        
        # Train initial model
        initial_model = RandomForestRegressor(random_state=42, n_estimators=10)
        initial_model.fit(X, y)
        
        # Save initial model
        initial_model_path = os.path.join(temp_dir, 'initial_model.pkl')
        with open(initial_model_path, 'wb') as f:
            pickle.dump(initial_model, f)
        
        # Retrain stable model
        stable_model_path = os.path.join(temp_dir, 'stable_model.pkl')
        decision = retrain_stable_model(initial_model_path, X, y, feature_cols, stable_model_path)
        
        assert isinstance(decision, dict)
        assert os.path.exists(stable_model_path)

    def test_run_sensitivity_analysis(self, sample_data, temp_dir):
        """Test sensitivity analysis."""
        from sklearn.ensemble import RandomForestRegressor
        
        feature_cols = ['mixing_enthalpy', 'atomic_size_mismatch', 'electronegativity_variance']
        target_col = 'critical_cooling_rate'
        
        X = sample_data[feature_cols]
        y = sample_data[target_col]
        
        # Train model
        model = RandomForestRegressor(random_state=42, n_estimators=10)
        model.fit(X, y)
        
        # Save model
        model_path = os.path.join(temp_dir, 'test_model.pkl')
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        
        # Run sensitivity analysis
        thresholds = [50, 100, 150]
        sensitivity_report = run_sensitivity_analysis(model_path, sample_data, target_col, thresholds)
        
        assert isinstance(sensitivity_report, dict)
        assert 'thresholds' in sensitivity_report
        assert 'rmse_continuous' in sensitivity_report
        assert 'f1_score' in sensitivity_report
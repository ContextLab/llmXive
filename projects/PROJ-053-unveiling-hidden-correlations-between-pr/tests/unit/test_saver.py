"""
Unit tests for the model saving functionality in models/saver.py.

These tests verify that models are correctly serialized and can be 
deserialized without data loss.
"""
import os
import sys
import tempfile
import pickle
import pytest
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C
from sklearn.linear_model import LinearRegression
import numpy as np

from models.saver import save_model, save_models
from config import get_models_dir


class TestSaveModel:
    """Tests for the save_model function."""
    
    def test_save_gpr_model(self, tmp_path):
        """Test saving a GPR model."""
        # Create a simple GPR model
        kernel = C(1.0) * RBF(1.0)
        gpr = GaussianProcessRegressor(kernel=kernel, random_state=42)
        
        # Create dummy training data
        X_train = np.random.rand(10, 2)
        y_train = np.random.rand(10)
        gpr.fit(X_train, y_train)
        
        # Mock the get_models_dir to use tmp_path
        with patch('models.saver.get_models_dir', return_value=str(tmp_path)):
            file_path = save_model(gpr, "test_gpr")
            
            # Verify file exists
            assert os.path.exists(file_path)
            assert file_path.endswith("test_gpr.pkl")
            
            # Verify file can be loaded
            with open(file_path, 'rb') as f:
                artifact = pickle.load(f)
            
            assert 'model' in artifact
            assert isinstance(artifact['model'], GaussianProcessRegressor)
            assert 'metadata' in artifact
            
    def test_save_model_with_metadata(self, tmp_path):
        """Test saving a model with custom metadata."""
        model = LinearRegression()
        X_train = np.random.rand(10, 2)
        y_train = np.random.rand(10)
        model.fit(X_train, y_train)
        
        metadata = {
            'custom_param': 'value',
            'number': 123,
            'nested': {'key': 'val'}
        }
        
        with patch('models.saver.get_models_dir', return_value=str(tmp_path)):
            file_path = save_model(model, "test_meta", metadata)
            
            with open(file_path, 'rb') as f:
                artifact = pickle.load(f)
            
            assert artifact['metadata'] == metadata
            
    def test_save_model_duplicate_name(self, tmp_path):
        """Test that saving a model with the same name overwrites."""
        model1 = LinearRegression()
        model2 = LinearRegression()
        
        X_train = np.random.rand(10, 2)
        y_train = np.random.rand(10)
        model1.fit(X_train, y_train)
        model2.fit(X_train, y_train * 2)  # Different fit
        
        with patch('models.saver.get_models_dir', return_value=str(tmp_path)):
            path1 = save_model(model1, "dup_test")
            path2 = save_model(model2, "dup_test")
            
            assert path1 == path2
            
            # Verify the second model is saved
            with open(path2, 'rb') as f:
                artifact = pickle.load(f)
            
            # The saved model should be model2
            # We can check by predicting on a known point
            test_point = np.array([[0.5, 0.5]])
            pred1 = model1.predict(test_point)[0]
            pred2 = model2.predict(test_point)[0]
            saved_pred = artifact['model'].predict(test_point)[0]
            
            # Allow for small floating point differences
            assert np.isclose(saved_pred, pred2, rtol=1e-5)


class TestSaveModels:
    """Tests for the save_models function."""
    
    def test_save_both_models(self, tmp_path):
        """Test saving both GPR and baseline models."""
        # Create models
        kernel = C(1.0) * RBF(1.0)
        gpr = GaussianProcessRegressor(kernel=kernel, random_state=42)
        baseline = LinearRegression()
        
        X_train = np.random.rand(20, 3)
        y_train = np.random.rand(20)
        
        gpr.fit(X_train, y_train)
        baseline.fit(X_train, y_train)
        
        gpr_meta = {'type': 'gpr', 'version': 1}
        baseline_meta = {'type': 'lr', 'version': 1}
        
        with patch('models.saver.get_models_dir', return_value=str(tmp_path)):
            paths = save_models(gpr, baseline, gpr_meta, baseline_meta)
            
            assert 'gpr_model_path' in paths
            assert 'baseline_model_path' in paths
            
            # Verify both files exist
            assert os.path.exists(paths['gpr_model_path'])
            assert os.path.exists(paths['baseline_model_path'])
            
            # Verify contents
            with open(paths['gpr_model_path'], 'rb') as f:
                gpr_artifact = pickle.load(f)
            assert isinstance(gpr_artifact['model'], GaussianProcessRegressor)
            assert gpr_artifact['metadata'] == gpr_meta
            
            with open(paths['baseline_model_path'], 'rb') as f:
                baseline_artifact = pickle.load(f)
            assert isinstance(baseline_artifact['model'], LinearRegression)
            assert baseline_artifact['metadata'] == baseline_meta

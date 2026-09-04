"""
Unit tests for Sparse Gaussian Process implementation.
"""

import os
import sys
import tempfile
import pytest
import numpy as np
import torch

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from models.sparse_gp import SparseGPModel, train_sparse_gp, save_model


class TestSparseGPModel:
    """Tests for the SparseGPModel class."""
    
    def test_initialization(self):
        """Test model initialization with various parameters."""
        num_features = 10
        num_inducing_points = 50
        
        model = SparseGPModel(num_features, num_inducing_points)
        
        assert model.variational_strategy.inducing_points.shape == (num_inducing_points, num_features)
        assert hasattr(model, 'mean_module')
        assert hasattr(model, 'covar_module')
        assert hasattr(model, 'likelihood')
    
    def test_forward_pass(self):
        """Test forward pass through the model."""
        num_features = 5
        num_inducing_points = 20
        batch_size = 10
        
        model = SparseGPModel(num_features, num_inducing_points)
        model.eval()
        
        x = torch.randn(batch_size, num_features)
        
        with torch.no_grad():
            output = model(x)
        
        assert output.mean.shape == (batch_size,)
        assert output.covariance_matrix.shape == (batch_size, batch_size)
    
    def test_prediction(self):
        """Test prediction method returns correct shapes."""
        num_features = 5
        num_inducing_points = 20
        test_size = 15
        
        model = SparseGPModel(num_features, num_inducing_points)
        model.eval()
        model.likelihood.eval()
        
        test_x = torch.randn(test_size, num_features)
        
        mean, variance = model.predict(test_x)
        
        assert isinstance(mean, np.ndarray)
        assert isinstance(variance, np.ndarray)
        assert mean.shape == (test_size,)
        assert variance.shape == (test_size,)
        assert np.all(variance >= 0)  # Variance should be non-negative


class TestTraining:
    """Tests for training functionality."""
    
    def test_training_basic(self):
        """Test basic training loop completes without error."""
        # Generate synthetic data
        np.random.seed(42)
        X = np.random.randn(100, 5)
        y = np.random.randn(100)
        
        # Train with minimal epochs
        model, likelihood = train_sparse_gp(
            X, y,
            num_inducing_points=20,
            max_epochs=5,
            learning_rate=0.01
        )
        
        assert model is not None
        assert likelihood is not None
        assert isinstance(model, SparseGPModel)
    
    def test_training_reproducibility(self):
        """Test that training with same seed produces same results."""
        np.random.seed(42)
        torch.manual_seed(42)
        
        X = np.random.randn(50, 3)
        y = np.random.randn(50)
        
        model1, likelihood1 = train_sparse_gp(X, y, num_inducing_points=10, max_epochs=3)
        
        # Reset seeds
        np.random.seed(42)
        torch.manual_seed(42)
        
        model2, likelihood2 = train_sparse_gp(X, y, num_inducing_points=10, max_epochs=3)
        
        # Compare initial inducing point locations (should be same due to seed)
        # Note: Due to potential numerical differences, we check if they're close
        inducing1 = model1.variational_strategy.inducing_points.numpy()
        inducing2 = model2.variational_strategy.inducing_points.numpy()
        
        assert np.allclose(inducing1, inducing2, atol=1e-6)

class TestModelSaving:
    """Tests for model saving functionality."""
    
    def test_save_and_load(self):
        """Test saving and loading a model."""
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = os.path.join(tmpdir, 'test_model.pt')
            
            # Create and train a simple model
            np.random.seed(42)
            X = np.random.randn(30, 4)
            y = np.random.randn(30)
            
            model, likelihood = train_sparse_gp(X, y, num_inducing_points=10, max_epochs=2)
            
            # Save model
            save_model(model, likelihood, model_path)
            
            # Verify file exists
            assert os.path.exists(model_path)
            
            # Load and verify
            checkpoint = torch.load(model_path, map_location='cpu')
            assert 'model_state_dict' in checkpoint
            assert 'likelihood_state_dict' in checkpoint
            assert 'num_features' in checkpoint
            assert 'num_inducing_points' in checkpoint
            
            # Verify dimensions
            assert checkpoint['num_features'] == 4
            assert checkpoint['num_inducing_points'] == 10

class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_small_dataset(self):
        """Test training with very small dataset."""
        np.random.seed(42)
        X = np.random.randn(10, 2)
        y = np.random.randn(10)
        
        # Should work with very small dataset
        model, likelihood = train_sparse_gp(X, y, num_inducing_points=5, max_epochs=2)
        assert model is not None
    
    def test_large_feature_space(self):
        """Test with larger feature space."""
        np.random.seed(42)
        X = np.random.randn(50, 20)
        y = np.random.randn(50)
        
        model, likelihood = train_sparse_gp(X, y, num_inducing_points=15, max_epochs=2)
        assert model is not None

if __name__ == '__main__':
    pytest.main([__file__, '-v'])

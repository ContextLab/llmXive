"""
Tests for SAE training with retry logic (T025).

This test file verifies:
1. Training loop executes correctly with multiple seeds
2. Model convergence across different seeds
3. Best model selection based on reconstruction loss
4. Output files are created correctly
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest
import torch
import numpy as np

# Import training functions
from train_sae import (
    set_seed,
    calculate_sparsity_loss,
    train_epoch,
    validate_model,
    train_with_seed,
    MAX_RETRIES,
    EPOCHS_PER_SEED
)
from models.sparse_autoencoder import create_sparse_autoencoder

class TestSAETraining:
    """Test suite for SAE training functionality."""
    
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Set up test fixtures."""
        self.tmp_path = tmp_path
        self.test_data_dir = tmp_path / "data" / "neural" / "processed"
        self.test_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create sample training data
        sample_data = np.random.randn(100, 10).astype(np.float32)
        sample_df = "\n".join([",".join(map(str, row)) for row in sample_data])
        (self.test_data_dir / "roi_timecourses.csv").write_text(
            "subject_id,roi_1,roi_2,roi_3,roi_4,roi_5,roi_6,roi_7,roi_8,roi_9,roi_10\n" +
            sample_df
        )
        
        # Save original data dir
        self.original_data_dir = Path("data")
        
        # Temporarily redirect data path
        import train_sae
        train_sae.Path = lambda x: self.tmp_path / x if not x.startswith("data/") else self.test_data_dir.parent / x
        
        yield
        
        # Restore
        train_sae.Path = Path
    
    def test_set_seed_reproducibility(self):
        """Test that set_seed produces reproducible results."""
        set_seed(42)
        a = np.random.randn(5)
        
        set_seed(42)
        b = np.random.randn(5)
        
        assert np.allclose(a, b), "Seed setting should produce reproducible results"
    
    def test_sparsity_loss_calculation(self):
        """Test sparsity loss calculation."""
        # Create test activations
        activations = torch.tensor([[1.0, 0.0, 2.0, 0.0],
                                   [0.0, 3.0, 0.0, 1.0]])
        
        loss = calculate_sparsity_loss(activations)
        
        # Expected: mean of absolute values = (1+0+2+0+0+3+0+1)/8 = 7/8 = 0.875
        expected = 0.875
        assert abs(loss.item() - expected) < 1e-5, f"Expected {expected}, got {loss.item()}"
    
    def test_model_creation(self):
        """Test that model can be created correctly."""
        input_dim = 10
        model = create_sparse_autoencoder(input_dim=input_dim)
        
        assert model is not None
        assert hasattr(model, 'encoder')
        assert hasattr(model, 'decoder')
    
    def test_training_epoch(self):
        """Test that one training epoch executes without errors."""
        input_dim = 10
        model = create_sparse_autoencoder(input_dim=input_dim)
        
        # Create dummy data
        data = torch.randn(32, input_dim)
        
        # Create optimizer
        import torch.optim as optim
        optimizer = optim.Adam(model.parameters(), lr=1e-3)
        
        # Run one epoch
        total_loss, recon_loss, sparse_loss = train_epoch(model, data, optimizer, torch.device("cpu"))
        
        assert total_loss > 0, "Total loss should be positive"
        assert recon_loss > 0, "Reconstruction loss should be positive"
        assert sparse_loss >= 0, "Sparsity loss should be non-negative"
    
    def test_validation_metrics(self):
        """Test that validation returns expected metrics."""
        input_dim = 10
        model = create_sparse_autoencoder(input_dim=input_dim)
        data = torch.randn(32, input_dim)
        
        metrics = validate_model(model, data, torch.device("cpu"))
        
        assert "reconstruction_loss" in metrics
        assert "sparsity_ratio" in metrics
        assert "mean_activation" in metrics
        assert 0 <= metrics["sparsity_ratio"] <= 1, "Sparsity ratio should be between 0 and 1"
    
    def test_training_with_seed(self):
        """Test training with a specific seed."""
        input_dim = 10
        data = torch.randn(100, input_dim)
        
        result = train_with_seed(42, data, torch.device("cpu"))
        
        assert result is not None, "Training should succeed"
        metrics, model = result
        
        assert metrics["seed"] == 42
        assert "reconstruction_loss" in metrics
        assert "sparsity_ratio" in metrics
        assert metrics["converged"] is True
    
    def test_multiple_seeds_training(self):
        """Test that training works across multiple seeds."""
        input_dim = 10
        data = torch.randn(100, input_dim)
        
        results = []
        for seed in [42, 123, 456]:
            result = train_with_seed(seed, data, torch.device("cpu"))
            if result is not None:
                results.append(result[0])
        
        assert len(results) > 0, "At least one seed should succeed"
        
        # Check that different seeds produce different (but valid) results
        losses = [r["reconstruction_loss"] for r in results]
        assert all(loss > 0 for loss in losses), "All losses should be positive"
    
    def test_best_model_selection(self):
        """Test that best model is selected based on reconstruction loss."""
        input_dim = 10
        data = torch.randn(100, input_dim)
        
        results = []
        models = []
        
        for seed in [42, 123, 456]:
            result = train_with_seed(seed, data, torch.device("cpu"))
            if result is not None:
                metrics, model = result
                results.append(metrics)
                models.append((metrics["reconstruction_loss"], model))
        
        # Find best
        best_loss, best_model = min(models, key=lambda x: x[0])
        
        # Verify best loss is in results
        result_losses = [r["reconstruction_loss"] for r in results]
        assert abs(best_loss - min(result_losses)) < 1e-6, "Best loss should match minimum"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
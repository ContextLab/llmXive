import os
import sys
import torch
import pytest
import numpy as np
import pandas as pd
import tempfile
import shutil
from pathlib import Path

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from models.baseline_nn import HeteroscedasticNN, negative_log_likelihood_loss, load_config, main

class TestHeteroscedasticNN:
    def test_parameter_count_limit(self):
        """Test that model stays under 10k parameters for typical input sizes."""
        input_dim = 20
        hidden_dim = 32
        model = HeteroscedasticNN(input_dim=input_dim, hidden_dim=hidden_dim)
        param_count = model.count_parameters()
        
        # Calculate expected params:
        # fc1: 20*32 + 32 = 672
        # fc2: 32*32 + 32 = 1056
        # mean_head: 32*1 + 1 = 33
        # var_head: 32*1 + 1 = 33
        # Total = 1794
        assert param_count <= 10000, f"Param count {param_count} exceeds 10k"
        assert param_count > 0

    def test_forward_pass_shapes(self):
        """Test that forward pass returns correct shapes."""
        input_dim = 10
        hidden_dim = 16
        model = HeteroscedasticNN(input_dim=input_dim, hidden_dim=hidden_dim)
        
        batch_size = 5
        x = torch.randn(batch_size, input_dim)
        
        mean, log_var = model(x)
        
        assert mean.shape == (batch_size, 1)
        assert log_var.shape == (batch_size, 1)

    def test_forward_pass_values(self):
        """Test that log_var is not constrained to be positive (it's log space)."""
        input_dim = 10
        hidden_dim = 16
        model = HeteroscedasticNN(input_dim=input_dim, hidden_dim=hidden_dim)
        
        x = torch.randn(5, input_dim)
        mean, log_var = model(x)
        
        # log_var can be negative (corresponding to variance < 1)
        # mean can be any value
        assert not torch.isnan(mean).any()
        assert not torch.isnan(log_var).any()

    def test_nll_loss_computation(self):
        """Test that NLL loss is computed correctly."""
        mean = torch.tensor([[0.0], [1.0]])
        log_var = torch.tensor([[0.0], [0.0]]) # variance = 1
        y = torch.tensor([[0.0], [2.0]])
        
        # Loss = 0.5 * (log_var + (y - mean)^2 / exp(log_var))
        # Sample 0: 0.5 * (0 + 0) = 0
        # Sample 1: 0.5 * (0 + 1) = 0.5
        # Mean = 0.25
        
        loss = negative_log_likelihood_loss(mean, log_var, y)
        expected = torch.tensor(0.25)
        
        assert torch.isclose(loss, expected, atol=1e-5)

    def test_nll_loss_gradient(self):
        """Test that gradients flow through the loss."""
        mean = torch.tensor([[0.0], [1.0]], requires_grad=True)
        log_var = torch.tensor([[0.0], [0.0]], requires_grad=True)
        y = torch.tensor([[0.0], [2.0]])
        
        loss = negative_log_likelihood_loss(mean, log_var, y)
        loss.backward()
        
        assert mean.grad is not None
        assert log_var.grad is not None
        assert not torch.isnan(mean.grad).any()
        assert not torch.isnan(log_var.grad).any()

def test_main_script_execution(tmp_path):
    """
    Test that the main script runs without error and produces output.
    This is a minimal integration test.
    """
    # Create temporary directories
    data_dir = tmp_path / "data" / "processed"
    data_dir.mkdir(parents=True)
    results_dir = tmp_path / "results" / "models"
    results_dir.mkdir(parents=True)
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir(parents=True)

    # Create dummy config
    config_path = tmp_path / "code" / "config.yaml"
    config_path.parent.mkdir(exist_ok=True)
    config_content = """
    seed: 42
    epochs: 2
    lr: 0.01
    hidden_dim: 16
    batch_size: 32
    """
    config_path.write_text(config_content)

    # Create dummy data
    # Features: 10 columns, Target: 1 column
    np.random.seed(42)
    n_samples = 100
    features = np.random.randn(n_samples, 10)
    target = np.random.randn(n_samples)
    
    train_df = pd.DataFrame(features, columns=[f"feat_{i}" for i in range(10)])
    train_df["target"] = target
    train_df["target_bin"] = 0
    train_df["sample_id"] = range(n_samples)
    
    val_df = train_df.copy()
    
    train_df.to_csv(data_dir / "features_train_20pca.csv", index=False)
    val_df.to_csv(data_dir / "features_val_20pca.csv", index=False)
    
    # Create dummy test file (required by load_processed_data)
    test_df = train_df.copy()
    test_df.to_csv(data_dir / "features_test_20pca.csv", index=False)

    # Create logs directory for pipeline.log
    (logs_dir / "pipeline.log").touch()

    # Patch sys.argv to simulate CLI call
    output_path = results_dir / "baseline_seed42.pt"
    sys.argv = [
        "baseline_nn.py",
        "--config", str(config_path),
        "--seed", "42",
        "--output", str(output_path)
    ]

    # Run main
    try:
        main()
    except SystemExit:
        pass # Expected if argparse is used outside CLI

    # Verify output exists
    assert output_path.exists(), f"Model file not created at {output_path}"

    # Verify model can be loaded
    checkpoint = torch.load(output_path, map_location='cpu')
    assert 'model_state_dict' in checkpoint
    assert checkpoint['seed'] == 42
    assert checkpoint['param_count'] <= 10000
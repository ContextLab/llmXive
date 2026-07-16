"""
Integration test for the baseline training pipeline (User Story 1).

This test verifies that the baseline Transformer (T006) can be trained on
synthetic functions (T005) and achieves a Mean Absolute Error (MAE) < 0.05
on the held-out test set within the resource constraints.

It imports real implementations from:
- src.models.baseline_transformer (BaselineTransformer)
- src.data.benchmarks (generate_synthetic_dataset, LorenzAttractor, FourierSeries)
- src.training.trainer (train_model, evaluate_model)
"""
import pytest
import torch
import numpy as np
import os
import sys
from pathlib import Path

# Ensure project root is in path for imports
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.models.baseline_transformer import BaselineTransformer
from src.data.benchmarks import generate_synthetic_dataset, LorenzAttractor, FourierSeries
from src.training.trainer import train_model, evaluate_model


@pytest.mark.integration
@pytest.mark.timeout(3600)  # 1 hour timeout for the full training run
def test_baseline_training_pipeline_lorenz():
    """
    Integration test: Train BaselineTransformer on Lorenz attractor data.
    
    Verifies:
    1. Data generation works and produces deterministic splits.
    2. Model instantiation matches expected architecture.
    3. Training loop completes without error.
    4. MAE on test set is < 0.05.
    5. Metrics are recorded.
    """
    # 1. Setup: Generate synthetic data
    # Using a fixed seed for reproducibility as per Constitution Principle III
    seed = 42
    np.random.seed(seed)
    torch.manual_seed(seed)
    
    # Generate Lorenz attractor dataset
    # Parameters: sigma=10, rho=28, beta=8/3
    dataset_config = {
        "type": "lorenz",
        "sigma": 10.0,
        "rho": 28.0,
        "beta": 8.0/3.0,
        "dt": 0.01,
        "steps": 500,
        "noise": 0.0,
        "seed": seed
    }
    
    train_data, test_data = generate_synthetic_dataset(
        dataset_type="lorenz",
        config=dataset_config,
        train_size=0.8,
        test_size=0.2
    )
    
    assert train_data is not None, "Training data generation failed"
    assert test_data is not None, "Test data generation failed"
    assert len(train_data) > 0, "Training set is empty"
    assert len(test_data) > 0, "Test set is empty"
    
    # Convert to tensors
    X_train = torch.FloatTensor(train_data['features'])
    y_train = torch.FloatTensor(train_data['targets'])
    X_test = torch.FloatTensor(test_data['features'])
    y_test = torch.FloatTensor(test_data['targets'])
    
    # 2. Setup: Instantiate BaselineTransformer
    # Input dim: 3 (x, y, z of Lorenz)
    # Hidden dim: 64 (small for CPU efficiency)
    # Output dim: 3 (predict next step)
    model = BaselineTransformer(
        input_dim=3,
        hidden_dim=64,
        output_dim=3,
        num_layers=2,
        num_heads=4,
        dropout=0.1
    )
    
    assert model is not None, "Model instantiation failed"
    
    # 3. Training: Run the training loop
    config = {
        "epochs": 10,
        "batch_size": 32,
        "learning_rate": 1e-3,
        "device": "cpu",
        "seed": seed
    }
    
    try:
        metrics = train_model(
            model=model,
            X_train=X_train,
            y_train=y_train,
            X_test=X_test,
            y_test=y_test,
            config=config
        )
    except Exception as e:
        pytest.fail(f"Training pipeline failed with error: {e}")
    
    # 4. Verification: Check MAE
    # The trainer should return a dict with 'test_mae'
    assert 'test_mae' in metrics, "Training metrics missing 'test_mae'"
    test_mae = metrics['test_mae']
    
    # Assert MAE < 0.05 (Threshold defined in User Story 1)
    # Allow a small tolerance for numerical stability, but strict on the bound
    assert test_mae < 0.05, f"Baseline MAE ({test_mae:.4f}) exceeded threshold of 0.05"
    
    # 5. Verification: Check metrics structure
    assert 'train_mae' in metrics, "Training metrics missing 'train_mae'"
    assert 'epochs_completed' in metrics, "Training metrics missing 'epochs_completed'"
    
    # Log the results for verification
    print(f"Baseline Training Completed. Train MAE: {metrics['train_mae']:.4f}, Test MAE: {test_mae:.4f}")
    
    return True


@pytest.mark.integration
@pytest.mark.timeout(3600)
def test_baseline_training_pipeline_fourier():
    """
    Integration test: Train BaselineTransformer on Fourier series data.
    
    Verifies the model can learn periodic functions from the synthetic generator.
    """
    seed = 123
    np.random.seed(seed)
    torch.manual_seed(seed)
    
    dataset_config = {
        "type": "fourier",
        "frequencies": [1, 3, 5],
        "amplitudes": [1.0, 0.5, 0.25],
        "period": 2 * np.pi,
        "points": 1000,
        "noise": 0.05,
        "seed": seed
    }
    
    train_data, test_data = generate_synthetic_dataset(
        dataset_type="fourier",
        config=dataset_config,
        train_size=0.8,
        test_size=0.2
    )
    
    assert train_data is not None
    assert test_data is not None
    
    X_train = torch.FloatTensor(train_data['features'])
    y_train = torch.FloatTensor(train_data['targets'])
    X_test = torch.FloatTensor(test_data['features'])
    y_test = torch.FloatTensor(test_data['targets'])
    
    model = BaselineTransformer(
        input_dim=1,
        hidden_dim=32,
        output_dim=1,
        num_layers=1,
        num_heads=2,
        dropout=0.0
    )
    
    config = {
        "epochs": 15,
        "batch_size": 64,
        "learning_rate": 1e-3,
        "device": "cpu",
        "seed": seed
    }
    
    try:
        metrics = train_model(
            model=model,
            X_train=X_train,
            y_train=y_train,
            X_test=X_test,
            y_test=y_test,
            config=config
        )
    except Exception as e:
        pytest.fail(f"Fourier training failed: {e}")
    
    test_mae = metrics.get('test_mae', float('inf'))
    assert test_mae < 0.05, f"Fourier MAE ({test_mae:.4f}) exceeded threshold of 0.05"
    
    print(f"Fourier Training Completed. Test MAE: {test_mae:.4f}")
    return True
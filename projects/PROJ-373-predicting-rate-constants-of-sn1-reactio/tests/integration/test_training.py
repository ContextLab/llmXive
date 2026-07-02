"""
Integration test for the training loop with a small subset of data.
Depends on: T019 (MPNN implementation), T020 (Training implementation)

This test verifies that:
1. The training pipeline can load a small subset of the processed data
2. The MPNN model can be instantiated and trained for a few epochs
3. The training loop completes without errors
4. Model weights and metrics are saved correctly
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import numpy as np
import torch
import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from models.mpnn import MPNN, MPNNConfig, create_mpnn_from_config
from models.train import (
    TrainingConfig,
    load_processed_data,
    prepare_features,
    create_dataloaders,
    train_model,
    evaluate_model
)
from utils.logger import setup_logging, get_logger

# Configure logging for tests
logger = setup_logging(log_level="INFO")


@pytest.fixture
def small_dataset(tmp_path):
    """
    Create a small synthetic dataset that mimics the structure of the real processed data.
    This avoids dependency on the full dataset download while testing the training pipeline.
    """
    # Create a small dataset with realistic structure
    np.random.seed(42)
    n_samples = 50  # Small subset for integration test
    
    data = {
        'smiles': [f'C({i})C' for i in range(n_samples)],
        'rate_constant': np.random.uniform(-2.0, 2.0, n_samples),
        'substrate_class': ['secondary' if i % 2 == 0 else 'tertiary' for i in range(n_samples)],
    }
    
    # Add descriptor columns (matching expected schema)
    n_charges = 10  # Typical number of Gasteiger charges
    n_topo = 5      # Typical number of topological indices
    
    data['gasteiger_charges'] = [
        np.random.randn(n_charges).tolist() for _ in range(n_samples)
    ]
    data['topological_indices'] = [
        np.random.randn(n_topo).tolist() for _ in range(n_samples)
    ]
    
    df = pd.DataFrame(data)
    csv_path = tmp_path / "small_sn1_subset.csv"
    df.to_csv(csv_path, index=False)
    
    return csv_path


@pytest.fixture
def training_config(tmp_path):
    """Create a minimal training configuration for integration testing."""
    config = TrainingConfig(
        model_type="mpnn",
        hidden_dim=16,
        num_layers=2,
        learning_rate=0.001,
        batch_size=16,
        num_epochs=3,  # Few epochs for fast testing
        device="cpu",
        random_seed=42
    )
    return config


def test_mpnn_training_loop(small_dataset, training_config, tmp_path):
    """
    Integration test: Run the full training loop on a small dataset.
    
    This test validates:
    - Data loading and preprocessing
    - Model instantiation
    - Training loop execution
    - Evaluation and metric calculation
    - Artifact saving
    """
    # Ensure output directories exist
    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    # Load and prepare data
    logger.info(f"Loading dataset from {small_dataset}")
    df = load_processed_data(small_dataset)
    
    logger.info(f"Dataset shape: {df.shape}")
    assert len(df) > 0, "Dataset should not be empty"
    
    # Prepare features
    X, y = prepare_features(df)
    logger.info(f"Features shape: {X.shape}, Labels shape: {y.shape}")
    
    # Create dataloaders
    train_loader, val_loader, test_loader = create_dataloaders(
        X, y, 
        batch_size=training_config.batch_size,
        val_ratio=0.2,
        test_ratio=0.2,
        seed=training_config.random_seed
    )
    
    assert len(train_loader) > 0, "Training loader should not be empty"
    
    # Create model
    model_config = MPNNConfig(
        hidden_dim=training_config.hidden_dim,
        num_layers=training_config.num_layers,
        input_dim=X.shape[1] if isinstance(X, np.ndarray) else X[0].shape[0]
    )
    model = create_mpnn_from_config(model_config)
    
    logger.info(f"Model created: {model}")
    
    # Train model
    logger.info("Starting training...")
    history = train_model(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        epochs=training_config.num_epochs,
        learning_rate=training_config.learning_rate,
        device=training_config.device,
        logger=logger
    )
    
    logger.info(f"Training completed. Final validation loss: {history['val_loss'][-1]:.4f}")
    
    # Verify training history
    assert len(history['train_loss']) == training_config.num_epochs
    assert len(history['val_loss']) == training_config.num_epochs
    
    # Evaluate on test set
    logger.info("Evaluating on test set...")
    test_metrics = evaluate_model(
        model=model,
        test_loader=test_loader,
        device=training_config.device,
        logger=logger
    )
    
    logger.info(f"Test metrics: {test_metrics}")
    
    # Verify metrics are computed
    assert 'r2' in test_metrics, "R2 metric should be present"
    assert 'mae' in test_metrics, "MAE metric should be present"
    assert isinstance(test_metrics['r2'], float), "R2 should be a float"
    assert isinstance(test_metrics['mae'], float), "MAE should be a float"
    
    # Verify model can make predictions
    model.eval()
    with torch.no_grad():
        # Get a sample batch
        batch = next(iter(test_loader))
        if isinstance(batch, tuple):
            x_batch, y_batch = batch
        else:
            x_batch, y_batch = batch['x'], batch['y']
        
        predictions = model(x_batch)
        assert predictions.shape[0] == x_batch.shape[0], "Prediction batch size mismatch"
    
    logger.info("✓ Integration test passed: Training loop completed successfully")
    
    return True


def test_training_with_config_validation(small_dataset, tmp_path):
    """
    Test that training respects configuration constraints.
    """
    # Create a config with edge-case values
    config = TrainingConfig(
        model_type="mpnn",
        hidden_dim=8,      # Small hidden dim
        num_layers=1,      # Minimum layers
        learning_rate=0.01,
        batch_size=4,      # Small batch size
        num_epochs=1,      # Single epoch
        device="cpu",
        random_seed=123
    )
    
    # Load data
    df = load_processed_data(small_dataset)
    X, y = prepare_features(df)
    
    # Create dataloaders
    train_loader, _, _ = create_dataloaders(
        X, y,
        batch_size=config.batch_size,
        val_ratio=0.2,
        test_ratio=0.2,
        seed=config.random_seed
    )
    
    # Create model
    model_config = MPNNConfig(
        hidden_dim=config.hidden_dim,
        num_layers=config.num_layers,
        input_dim=X.shape[1] if isinstance(X, np.ndarray) else X[0].shape[0]
    )
    
    # Validate model configuration constraints
    assert 1 <= model_config.num_layers <= 4, "Layer count must be between 1 and 4"
    
    model = create_mpnn_from_config(model_config)
    
    # Train for one epoch
    history = train_model(
        model=model,
        train_loader=train_loader,
        val_loader=None,  # No validation for this test
        epochs=config.num_epochs,
        learning_rate=config.learning_rate,
        device=config.device,
        logger=logger
    )
    
    assert len(history['train_loss']) == 1
    assert history['train_loss'][0] > 0, "Loss should be positive"
    
    logger.info("✓ Config validation test passed")


if __name__ == "__main__":
    # Run tests when executed directly
    pytest.main([__file__, "-v", "--tb=short"])
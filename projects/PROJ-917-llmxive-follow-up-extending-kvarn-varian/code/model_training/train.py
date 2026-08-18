"""
Training script for the Static Prior MLP model.

Implements the training loop with MSE loss, CPU-only execution,
and epoch logging as per T023 requirements.

Outputs:
    - data/models/mlp_weights.pt: Trained model weights
    - data/metrics/training_log.csv: Training metrics per epoch
"""
import os
import sys
import logging
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

# Import project modules based on provided API surface
from config import get_config
from data_generation.utils import load_from_parquet
from model_training.mlp_model import StaticPriorMLP, create_model
from model_training.seed_config import parse_seed_args, main as seed_main

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)

def load_training_data(
    data_path: str,
    feature_cols: list,
    target_col: str,
    test_split_ratio: float = 0.2
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    Load data from Parquet, split into train/test sets.
    
    Args:
        data_path: Path to the input Parquet file
        feature_cols: List of column names to use as features
        target_col: Column name for the target variable
        test_split_ratio: Fraction of data to use for testing
        
    Returns:
        Tuple of (X_train, X_test, y_train, y_test) as torch tensors
    """
    logger.info(f"Loading data from {data_path}")
    df = load_from_parquet(data_path)
    
    if df is None:
        raise FileNotFoundError(f"Could not load data from {data_path}")
    
    # Extract features and target
    X = df[feature_cols].values.astype(np.float32)
    y = df[target_col].values.astype(np.float32)
    
    # Handle any remaining NaN/Inf values by dropping rows
    valid_mask = np.isfinite(X).all(axis=1) & np.isfinite(y)
    X = X[valid_mask]
    y = y[valid_mask]
    
    logger.info(f"Loaded {len(y)} samples after cleaning")
    
    if len(y) == 0:
        raise ValueError("No valid data remaining after cleaning")
    
    # Shuffle data
    indices = np.random.permutation(len(y))
    X = X[indices]
    y = y[indices]
    
    # Split into train/test
    split_idx = int(len(y) * (1 - test_split_ratio))
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    
    logger.info(f"Train size: {len(y_train)}, Test size: {len(y_test)}")
    
    # Convert to PyTorch tensors
    X_train_tensor = torch.from_numpy(X_train)
    X_test_tensor = torch.from_numpy(X_test)
    y_train_tensor = torch.from_numpy(y_train).unsqueeze(1)
    y_test_tensor = torch.from_numpy(y_test).unsqueeze(1)
    
    return X_train_tensor, X_test_tensor, y_train_tensor, y_test_tensor

def train_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: torch.device
) -> Dict[str, float]:
    """
    Train for one epoch.
    
    Args:
        model: The neural network model
        dataloader: DataLoader for training data
        criterion: Loss function
        optimizer: Optimizer for parameter updates
        device: Device to run training on
        
    Returns:
        Dictionary containing epoch metrics (loss)
    """
    model.train()
    total_loss = 0.0
    num_batches = 0
    
    for batch_X, batch_y in dataloader:
        batch_X = batch_X.to(device)
        batch_y = batch_y.to(device)
        
        # Forward pass
        optimizer.zero_grad()
        outputs = model(batch_X)
        loss = criterion(outputs, batch_y)
        
        # Backward pass
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        num_batches += 1
    
    avg_loss = total_loss / num_batches if num_batches > 0 else 0.0
    return {"loss": avg_loss}

def evaluate_model(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    device: torch.device
) -> Dict[str, float]:
    """
    Evaluate model on a dataset.
    
    Args:
        model: The neural network model
        dataloader: DataLoader for evaluation data
        criterion: Loss function
        device: Device to run evaluation on
        
    Returns:
        Dictionary containing evaluation metrics (loss, MSE)
    """
    model.eval()
    total_loss = 0.0
    total_mse = 0.0
    num_batches = 0
    
    with torch.no_grad():
        for batch_X, batch_y in dataloader:
            batch_X = batch_X.to(device)
            batch_y = batch_y.to(device)
            
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            mse = torch.mean((outputs - batch_y) ** 2)
            
            total_loss += loss.item()
            total_mse += mse.item()
            num_batches += 1
    
    avg_loss = total_loss / num_batches if num_batches > 0 else 0.0
    avg_mse = total_mse / num_batches if num_batches > 0 else 0.0
    
    return {"loss": avg_loss, "mse": avg_mse}

def run_training(
    data_path: str,
    model_path: str,
    log_path: str,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Main training loop.
    
    Args:
        data_path: Path to input Parquet file
        model_path: Path to save trained model weights
        log_path: Path to save training log CSV
        config: Training configuration dictionary
        
    Returns:
        Dictionary containing final training results
    """
    # Ensure output directories exist
    Path(model_path).parent.mkdir(parents=True, exist_ok=True)
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Set device (CPU-only as per requirements)
    device = torch.device("cpu")
    logger.info(f"Using device: {device}")
    
    # Load data
    feature_cols = config.get("feature_cols", ["mean", "variance"])
    target_col = config.get("target_col", "scaling_factor")
    test_split_ratio = config.get("test_split_ratio", 0.2)
    
    X_train, X_test, y_train, y_test = load_training_data(
        data_path, feature_cols, target_col, test_split_ratio
    )
    
    # Create datasets and dataloaders
    train_dataset = TensorDataset(X_train, y_train)
    test_dataset = TensorDataset(X_test, y_test)
    
    batch_size = config.get("batch_size", 32)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
    
    # Initialize model
    input_dim = X_train.shape[1]
    hidden_dims = config.get("hidden_dims", [64, 32])
    model = create_model(input_dim, hidden_dims).to(device)
    
    logger.info(f"Model architecture:\n{model}")
    
    # Define loss and optimizer
    criterion = nn.MSELoss()
    learning_rate = config.get("learning_rate", 1e-3)
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    
    # Training loop
    num_epochs = config.get("num_epochs", 100)
    patience = config.get("patience", 10)
    log_epochs = config.get("log_epochs", 1)
    
    best_val_loss = float("inf")
    patience_counter = 0
    training_log = []
    
    logger.info(f"Starting training for {num_epochs} epochs...")
    start_time = time.time()
    
    for epoch in range(num_epochs):
        # Train one epoch
        train_metrics = train_epoch(model, train_loader, criterion, optimizer, device)
        
        # Evaluate on test set
        val_metrics = evaluate_model(model, test_loader, criterion, device)
        
        # Log metrics
        if (epoch + 1) % log_epochs == 0:
            epoch_log = {
                "epoch": epoch + 1,
                "train_loss": train_metrics["loss"],
                "val_loss": val_metrics["loss"],
                "val_mse": val_metrics["mse"],
                "learning_rate": optimizer.param_groups[0]["lr"]
            }
            training_log.append(epoch_log)
            logger.info(
                f"Epoch {epoch+1}/{num_epochs} - "
                f"Train Loss: {train_metrics['loss']:.6f}, "
                f"Val Loss: {val_metrics['loss']:.6f}, "
                f"Val MSE: {val_metrics['mse']:.6f}"
            )
        
        # Early stopping check
        if val_metrics["loss"] < best_val_loss:
            best_val_loss = val_metrics["loss"]
            patience_counter = 0
            # Save best model
            torch.save(model.state_dict(), model_path)
            logger.info(f"Saved best model to {model_path}")
        else:
            patience_counter += 1
            if patience_counter >= patience:
                logger.info(f"Early stopping at epoch {epoch+1}")
                break
    
    end_time = time.time()
    training_duration = end_time - start_time
    
    # Save training log
    log_df = pd.DataFrame(training_log)
    log_df.to_csv(log_path, index=False)
    logger.info(f"Training log saved to {log_path}")
    
    # Final evaluation
    final_metrics = evaluate_model(model, test_loader, criterion, device)
    
    results = {
        "num_epochs_completed": len(training_log),
        "best_val_loss": best_val_loss,
        "final_val_loss": final_metrics["loss"],
        "final_val_mse": final_metrics["mse"],
        "training_duration_seconds": training_duration,
        "model_path": model_path,
        "log_path": log_path
    }
    
    logger.info(f"Training completed. Final MSE: {final_metrics['mse']:.6f}")
    return results

def main():
    """Main entry point for the training script."""
    # Parse command line arguments for seed
    args = parse_seed_args()
    
    # Load configuration
    config = get_config()
    
    # Override with command line args if provided
    if args.learning_rate is not None:
        config.learning_rate = args.learning_rate
    if args.batch_size is not None:
        config.batch_size = args.batch_size
    if args.num_epochs is not None:
        config.num_epochs = args.num_epochs
    if args.hidden_dims is not None:
        config.hidden_dims = [int(x) for x in args.hidden_dims.split(",")]
    
    # Set random seed
    if hasattr(config, 'random_seed'):
        np.random.seed(config.random_seed)
        torch.manual_seed(config.random_seed)
        logger.info(f"Set random seed to {config.random_seed}")
    
    # Define paths
    project_root = Path(__file__).resolve().parent.parent.parent
    data_path = project_root / "data" / "raw" / "synthetic_attention_matrices.parquet"
    model_path = project_root / "data" / "models" / "mlp_weights.pt"
    log_path = project_root / "data" / "metrics" / "training_log.csv"
    
    # Training configuration
    training_config = {
        "feature_cols": ["mean", "variance"],
        "target_col": "scaling_factor",
        "test_split_ratio": 0.2,
        "batch_size": getattr(config, 'batch_size', 32),
        "learning_rate": getattr(config, 'learning_rate', 1e-3),
        "num_epochs": getattr(config, 'num_epochs', 100),
        "hidden_dims": getattr(config, 'hidden_dims', [64, 32]),
        "patience": 10,
        "log_epochs": 1
    }
    
    logger.info(f"Training configuration: {json.dumps(training_config, indent=2)}")
    
    # Run training
    try:
        results = run_training(
            data_path=str(data_path),
            model_path=str(model_path),
            log_path=str(log_path),
            config=training_config
        )
        
        # Save results summary
        results_path = project_root / "data" / "metrics" / "training_results.json"
        with open(results_path, "w") as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Training results saved to {results_path}")
        return 0
        
    except Exception as e:
        logger.error(f"Training failed: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
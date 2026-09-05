"""
Training loop for the Static Prior MLP model.
Handles data loading, training epochs, evaluation, and artifact persistence.
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

# Local imports based on API surface
from config import get_config
from model_training.mlp_model import StaticPriorMLP, create_model
from model_training.baselines import evaluate_baseline_mse
from data_generation.utils import get_project_root, setup_generation_logger

# Configure logger
logger = logging.getLogger(__name__)

def load_training_data(csv_path: Optional[str] = None) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    Loads the synthetic attention matrix statistics and scaling factors from CSV.
    Returns: (train_X, train_y, test_X, test_y) as torch tensors.
    """
    if csv_path is None:
        project_root = get_project_root()
        csv_path = str(project_root / "data" / "raw" / "synthetic_attention_matrices.csv")
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Training data not found at {csv_path}. Run data generation first.")
    
    logger.info(f"Loading training data from {csv_path}")
    df = pd.read_csv(csv_path)
    
    # Select features: mean, variance (as per T022/FR-002)
    # Ensure columns exist
    required_cols = ['mean', 'variance', 'scaling_factor']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in dataset: {missing}")
    
    X = df[['mean', 'variance']].values.astype(np.float32)
    y = df['scaling_factor'].values.astype(np.float32)
    
    # Simple 80/20 split
    n = len(X)
    indices = np.arange(n)
    np.random.seed(get_config().RANDOM_SEED)
    np.random.shuffle(indices)
    
    split_idx = int(0.8 * n)
    train_idx = indices[:split_idx]
    test_idx = indices[split_idx:]
    
    train_X = torch.tensor(X[train_idx], dtype=torch.float32)
    train_y = torch.tensor(y[train_idx], dtype=torch.float32).view(-1, 1)
    test_X = torch.tensor(X[test_idx], dtype=torch.float32)
    test_y = torch.tensor(y[test_idx], dtype=torch.float32).view(-1, 1)
    
    logger.info(f"Loaded {n} samples. Train: {len(train_X)}, Test: {len(test_X)}")
    return train_X, train_y, test_X, test_y

def train_epoch(model: nn.Module, dataloader: DataLoader, optimizer: torch.optim.Optimizer, criterion: nn.Module, device: torch.device) -> float:
    """
    Executes one epoch of training.
    Returns: Average loss for the epoch.
    """
    model.train()
    total_loss = 0.0
    num_batches = 0
    
    for batch_X, batch_y in dataloader:
        batch_X, batch_y = batch_X.to(device), batch_y.to(device)
        
        optimizer.zero_grad()
        outputs = model(batch_X)
        loss = criterion(outputs, batch_y)
        
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        num_batches += 1
    
    return total_loss / num_batches if num_batches > 0 else 0.0

def evaluate_model(model: nn.Module, dataloader: DataLoader, criterion: nn.Module, device: torch.device) -> float:
    """
    Evaluates the model on a dataset.
    Returns: Average loss (MSE) for the dataset.
    """
    model.eval()
    total_loss = 0.0
    num_batches = 0
    
    with torch.no_grad():
        for batch_X, batch_y in dataloader:
            batch_X, batch_y = batch_X.to(device), batch_y.to(device)
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            total_loss += loss.item()
            num_batches += 1
    
    return total_loss / num_batches if num_batches > 0 else 0.0

def run_training(train_X: torch.Tensor, train_y: torch.Tensor, 
                 test_X: torch.Tensor, test_y: torch.Tensor,
                 config: Any) -> Dict[str, Any]:
    """
    Runs the full training loop, evaluates, and returns metrics.
    Does NOT save artifacts here; that is handled by main() to ensure
    the training logic remains pure and testable.
    """
    device = torch.device("cpu") # Enforce CPU-only per spec
    if not config.CPU_ONLY:
        logger.warning("Config says CPU_ONLY=False, but forcing CPU for consistency.")
    
    model = create_model(input_dim=2, hidden_dim=64, output_dim=1)
    model = model.to(device)
    
    # Hyperparameters from config or defaults
    learning_rate = getattr(config, 'LEARNING_RATE', 1e-3)
    batch_size = getattr(config, 'BATCH_SIZE', 256)
    epochs = getattr(config, 'EPOCHS', 100)
    
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    criterion = nn.MSELoss()
    
    train_dataset = TensorDataset(train_X, train_y)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    
    test_dataset = TensorDataset(test_X, test_y)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
    
    history = {
        'train_loss': [],
        'test_loss': [],
        'epoch_time': []
    }
    
    logger.info(f"Starting training for {epochs} epochs on {device}")
    
    for epoch in range(epochs):
        start_time = time.time()
        train_loss = train_epoch(model, train_loader, optimizer, criterion, device)
        test_loss = evaluate_model(model, test_loader, criterion, device)
        epoch_time = time.time() - start_time
        
        history['train_loss'].append(train_loss)
        history['test_loss'].append(test_loss)
        history['epoch_time'].append(epoch_time)
        
        if (epoch + 1) % 10 == 0:
            logger.info(f"Epoch [{epoch+1}/{epochs}] - Train Loss: {train_loss:.6f}, Test Loss: {test_loss:.6f}, Time: {epoch_time:.2f}s")
    
    # Final evaluation
    final_train_loss = history['train_loss'][-1]
    final_test_loss = history['test_loss'][-1]
    
    # Calculate baseline MSE for comparison (FR-009)
    baseline_mse = evaluate_baseline_mse(test_X.numpy(), test_y.numpy())
    
    metrics = {
        'final_train_loss': final_train_loss,
        'final_test_loss': final_test_loss,
        'baseline_mse': baseline_mse,
        'epochs': epochs,
        'learning_rate': learning_rate,
        'batch_size': batch_size,
        'model_architecture': 'MLP(2 -> 64 -> 64 -> 1)',
        'history': history
    }
    
    return model, metrics

def save_artifacts(model: nn.Module, metrics: Dict[str, Any], config: Any) -> Dict[str, str]:
    """
    Saves the trained model weights and training metrics to disk.
    Returns a dictionary of paths to the saved artifacts.
    """
    project_root = get_project_root()
    
    # Ensure directories exist
    model_dir = project_root / "data" / "models"
    metrics_dir = project_root / "data" / "metrics"
    model_dir.mkdir(parents=True, exist_ok=True)
    metrics_dir.mkdir(parents=True, exist_ok=True)
    
    model_path = model_dir / "mlp_weights.pt"
    metrics_path = metrics_dir / "training_log.csv"
    
    # Save model weights
    torch.save({
        'model_state_dict': model.state_dict(),
        'config': {
            'input_dim': 2,
            'hidden_dim': 64,
            'output_dim': 1,
            'learning_rate': metrics['learning_rate'],
            'batch_size': metrics['batch_size'],
            'epochs': metrics['epochs']
        }
    }, str(model_path))
    logger.info(f"Model weights saved to {model_path}")
    
    # Save metrics to CSV
    # Flatten history for CSV row
    history = metrics.pop('history')
    metrics['train_loss_history'] = json.dumps(history['train_loss'])
    metrics['test_loss_history'] = json.dumps(history['test_loss'])
    metrics['epoch_time_history'] = json.dumps(history['epoch_time'])
    
    df_metrics = pd.DataFrame([metrics])
    df_metrics.to_csv(metrics_path, index=False)
    logger.info(f"Training metrics saved to {metrics_path}")
    
    return {
        'model_weights': str(model_path),
        'training_log': str(metrics_path)
    }

def main():
    """
    Main entry point for the training script.
    Orchestrates loading, training, and saving.
    """
    # Setup logging
    log_dir = get_project_root() / "logs"
    log_dir.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "training.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    config = get_config()
    logger.info("Starting Static Prior Model Training")
    
    try:
        # 1. Load Data
        train_X, train_y, test_X, test_y = load_training_data()
        
        # 2. Train Model
        model, metrics = run_training(train_X, train_y, test_X, test_y, config)
        
        # 3. Save Artifacts (T026 Requirement)
        paths = save_artifacts(model, metrics, config)
        
        logger.info("Training completed successfully.")
        logger.info(f"Artifacts saved: {paths}")
        
        # Print summary
        print(f"\n=== Training Summary ===")
        print(f"Final Test MSE: {metrics['final_test_loss']:.6f}")
        print(f"Baseline MSE (1/var): {metrics['baseline_mse']:.6f}")
        print(f"Improvement: {'Yes' if metrics['final_test_loss'] < metrics['baseline_mse'] else 'No'}")
        
    except Exception as e:
        logger.error(f"Training failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
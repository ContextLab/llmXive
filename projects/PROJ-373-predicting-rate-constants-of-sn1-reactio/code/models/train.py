"""
Train MPNN model with Random Search Hyperparameter Optimization.

This script performs random search over hyperparameter configurations (<=50),
trains the MPNN model on the prepared dataset, and saves the best model and
metrics to the artifacts directory.
"""
import os
import sys
import json
import logging
import random
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import time

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

# Project imports
from config import ensure_dirs
from utils.logger import setup_logging, get_logger
from models.mpnn import MPNN, MPNNConfig, create_mpnn_from_config

# Constants
MAX_CONFIGURATIONS = 50
RANDOM_SEED = 42
DEVICE = torch.device("cpu")  # CPU-only constraint

@dataclass
class TrainingConfig:
    """Configuration for the training run."""
    num_configs: int = MAX_CONFIGURATIONS
    patience: int = 5
    max_epochs: int = 100
    learning_rate_range: Tuple[float, float] = (1e-5, 1e-2)
    hidden_dim_range: Tuple[int, int] = (32, 256)
    num_layers_range: Tuple[int, int] = (1, 4)
    dropout_range: Tuple[float, float] = (0.0, 0.3)
    batch_size: int = 32
    weight_decay_range: Tuple[float, float] = (0.0, 1e-4)

def load_processed_data(data_path: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load the stratified train/val/test datasets."""
    train_path = Path(data_path) / "train.csv"
    val_path = Path(data_path) / "val.csv"
    test_path = Path(data_path) / "test.csv"
    
    if not (train_path.exists() and val_path.exists() and test_path.exists()):
        raise FileNotFoundError(
            f"Split datasets not found. Expected: {train_path}, {val_path}, {test_path}"
        )
    
    train_df = pd.read_csv(train_path)
    val_df = pd.read_csv(val_path)
    test_df = pd.read_csv(test_path)
    
    return train_df, val_df, test_df

def prepare_features(df: pd.DataFrame, scaler: Optional[StandardScaler] = None, fit: bool = False) -> Tuple[np.ndarray, np.ndarray, StandardScaler]:
    """
    Prepare feature matrix and target vector from dataframe.
    
    Args:
        df: DataFrame with descriptor columns and 'rate_constant' target
        scaler: Optional pre-fitted scaler
        fit: Whether to fit the scaler on this data
        
    Returns:
        X: Feature matrix (normalized)
        y: Target vector (log-transformed rate constants)
        scaler: Fitted StandardScaler
    """
    # Identify descriptor columns (exclude metadata)
    exclude_cols = ['smiles', 'rate_constant', 'substrate_class', 'source_id']
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    if not feature_cols:
        raise ValueError("No feature columns found in dataset")
        
    X = df[feature_cols].values.astype(np.float32)
    y = np.log1p(df['rate_constant'].values.astype(np.float32))  # Log transform target
    
    if fit:
        scaler = StandardScaler()
        X = scaler.fit_transform(X)
    else:
        if scaler is None:
            raise ValueError("Scaler must be provided if not fitting")
        X = scaler.transform(X)
        
    return X, y, scaler

def create_dataloaders(train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame, 
                      batch_size: int, device: torch.device) -> Tuple[DataLoader, DataLoader, DataLoader, StandardScaler]:
    """Create PyTorch DataLoaders from dataframes."""
    # Fit scaler on training data
    X_train, y_train, scaler = prepare_features(train_df, fit=True)
    X_val, y_val, _ = prepare_features(val_df, scaler=scaler, fit=False)
    X_test, y_test, _ = prepare_features(test_df, scaler=scaler, fit=False)
    
    # Convert to tensors
    train_dataset = TensorDataset(
        torch.tensor(X_train, dtype=torch.float32),
        torch.tensor(y_train, dtype=torch.float32)
    )
    val_dataset = TensorDataset(
        torch.tensor(X_val, dtype=torch.float32),
        torch.tensor(y_val, dtype=torch.float32)
    )
    test_dataset = TensorDataset(
        torch.tensor(X_test, dtype=torch.float32),
        torch.tensor(y_test, dtype=torch.float32)
    )
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
    
    return train_loader, val_loader, test_loader, scaler

def generate_random_config(config: TrainingConfig) -> Dict[str, Any]:
    """Generate a single random hyperparameter configuration."""
    return {
        'learning_rate': random.uniform(*config.learning_rate_range),
        'hidden_dim': random.choice([32, 64, 128, 256]),
        'num_layers': random.randint(*config.num_layers_range),
        'dropout': random.uniform(*config.dropout_range),
        'weight_decay': random.uniform(*config.weight_decay_range),
    }

def evaluate_model(model: MPNN, dataloader: DataLoader, criterion: nn.Module, device: torch.device) -> Tuple[float, float]:
    """Evaluate model on a dataset, returning MSE and MAE."""
    model.eval()
    total_loss = 0.0
    total_mae = 0.0
    n_samples = 0
    
    with torch.no_grad():
        for X_batch, y_batch in dataloader:
            X_batch, y_batch = X_batch.to(device), y_batch.to(device)
            y_pred = model(X_batch)
            
            loss = criterion(y_pred, y_batch)
            total_loss += loss.item() * X_batch.size(0)
            total_mae += torch.abs(y_pred - y_batch).sum().item()
            n_samples += X_batch.size(0)
    
    return total_loss / n_samples, total_mae / n_samples

def train_epoch(model: MPNN, dataloader: DataLoader, optimizer: optim.Optimizer, 
               criterion: nn.Module, device: torch.device) -> float:
    """Train for one epoch, returning average loss."""
    model.train()
    total_loss = 0.0
    n_samples = 0
    
    for X_batch, y_batch in dataloader:
        X_batch, y_batch = X_batch.to(device), y_batch.to(device)
        
        optimizer.zero_grad()
        y_pred = model(X_batch)
        loss = criterion(y_pred, y_batch)
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item() * X_batch.size(0)
        n_samples += X_batch.size(0)
    
    return total_loss / n_samples

def train_model(model: MPNN, train_loader: DataLoader, val_loader: DataLoader,
               config: MPNNConfig, training_cfg: TrainingConfig, 
               device: torch.device, logger: logging.Logger) -> Tuple[MPNN, Dict[str, Any]]:
    """Train a single model instance with early stopping."""
    optimizer = optim.Adam(model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=3)
    criterion = nn.MSELoss()
    
    best_val_loss = float('inf')
    best_model_state = None
    patience_counter = 0
    training_history = []
    
    for epoch in range(training_cfg.max_epochs):
        train_loss = train_epoch(model, train_loader, optimizer, criterion, device)
        val_loss, val_mae = evaluate_model(model, val_loader, criterion, device)
        
        scheduler.step(val_loss)
        
        training_history.append({
            'epoch': epoch + 1,
            'train_loss': train_loss,
            'val_loss': val_loss,
            'val_mae': val_mae
        })
        
        logger.debug(f"Epoch {epoch+1}: Train Loss={train_loss:.4f}, Val Loss={val_loss:.4f}, Val MAE={val_mae:.4f}")
        
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_model_state = model.state_dict().copy()
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= training_cfg.patience:
                logger.info(f"Early stopping at epoch {epoch+1}")
                break
    
    # Load best model
    if best_model_state is not None:
        model.load_state_dict(best_model_state)
    
    # Final evaluation
    final_train_loss, final_train_mae = evaluate_model(model, train_loader, criterion, device)
    final_val_loss, final_val_mae = evaluate_model(model, val_loader, criterion, device)
    
    metrics = {
        'best_val_loss': best_val_loss,
        'final_train_loss': final_train_loss,
        'final_train_mae': final_train_mae,
        'final_val_loss': final_val_loss,
        'final_val_mae': final_val_mae,
        'epochs_trained': len(training_history),
        'learning_rate': config.learning_rate,
        'hidden_dim': config.hidden_dim,
        'num_layers': config.num_layers,
        'dropout': config.dropout,
        'weight_decay': config.weight_decay,
    }
    
    return model, metrics

def run_random_search(train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame,
                     training_cfg: TrainingConfig, device: torch.device, logger: logging.Logger) -> Tuple[MPNN, MPNNConfig, Dict[str, Any], List[Dict[str, Any]]]:
    """Run random search hyperparameter optimization."""
    logger.info(f"Starting random search with {training_cfg.num_configs} configurations")
    
    train_loader, val_loader, test_loader, scaler = create_dataloaders(
        train_df, val_df, test_df, training_cfg.batch_size, device
    )
    
    search_history = []
    best_model = None
    best_config = None
    best_metrics = None
    
    for i in range(training_cfg.num_configs):
        logger.info(f"Configuration {i+1}/{training_cfg.num_configs}")
        
        # Generate random config
        hp_config = generate_random_config(training_cfg)
        
        # Create MPNN config
        # Note: We need input_dim from the data
        input_dim = train_df.shape[1] - 4  # Exclude metadata columns
        mpnn_config = MPNNConfig(
            input_dim=input_dim,
            output_dim=1,
            hidden_dim=hp_config['hidden_dim'],
            num_layers=hp_config['num_layers'],
            dropout=hp_config['dropout'],
            learning_rate=hp_config['learning_rate'],
            weight_decay=hp_config['weight_decay']
        )
        
        # Create and train model
        try:
            model = create_mpnn_from_config(mpnn_config)
            model.to(device)
            
            trained_model, metrics = train_model(
                model, train_loader, val_loader, mpnn_config, training_cfg, device, logger
            )
            
            # Record results
            result = {**hp_config, **metrics}
            search_history.append(result)
            
            # Update best model
            if best_model is None or metrics['best_val_loss'] < best_metrics['best_val_loss']:
                best_model = trained_model
                best_config = mpnn_config
                best_metrics = metrics
                logger.info(f"New best model found: Val Loss={metrics['best_val_loss']:.4f}")
            
        except Exception as e:
            logger.error(f"Configuration {i+1} failed: {e}")
            search_history.append({'config': hp_config, 'error': str(e)})
            continue
    
    return best_model, best_config, best_metrics, search_history

def save_results(best_model: MPNN, best_config: MPNNConfig, best_metrics: Dict[str, Any],
                search_history: List[Dict[str, Any]], artifacts_dir: str):
    """Save best model weights and metrics."""
    artifacts_path = Path(artifacts_dir)
    ensure_dirs(artifacts_path)
    
    # Save model weights
    model_path = artifacts_path / "best_model.pt"
    torch.save({
        'model_state_dict': best_model.state_dict(),
        'config': asdict(best_config),
    }, model_path)
    logging.info(f"Saved best model to {model_path}")
    
    # Save metrics
    metrics_path = artifacts_path / "metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(best_metrics, f, indent=2)
    logging.info(f"Saved metrics to {metrics_path}")
    
    # Save search history
    search_log_path = artifacts_path / "hyperparameter_search.log"
    with open(search_log_path, 'w') as f:
        for entry in search_history:
            f.write(json.dumps(entry) + '\n')
    logging.info(f"Saved search history to {search_log_path}")

def main():
    """Main entry point for training script."""
    # Setup
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data" / "processed"
    artifacts_dir = project_root / "artifacts"
    
    logger = setup_logging(project_root)
    logger.info("Starting MPNN training with random search")
    
    # Load data
    try:
        train_df, val_df, test_df = load_processed_data(str(data_dir))
        logger.info(f"Loaded data: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    # Configuration
    training_cfg = TrainingConfig()
    device = DEVICE
    
    # Run random search
    best_model, best_config, best_metrics, search_history = run_random_search(
        train_df, val_df, test_df, training_cfg, device, logger
    )
    
    if best_model is None:
        logger.error("No valid model was trained. Exiting.")
        sys.exit(1)
    
    # Save results
    save_results(best_model, best_config, best_metrics, search_history, str(artifacts_dir))
    
    logger.info("Training completed successfully")
    logger.info(f"Best Model Metrics: {json.dumps(best_metrics, indent=2)}")

if __name__ == "__main__":
    main()
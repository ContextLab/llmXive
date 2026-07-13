from __future__ import annotations

import argparse
import csv
import os
import random
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm

# Local imports from project structure
from models.schnet_gnn import SchNetGNN
from training.evaluate import mae, rmse
from training.split_data import get_train_test_splits
from utils.reproducibility import set_seed
from utils.pipeline_time_limit import time_limit
from utils.cpu_constraint import cpu_limit
from utils.memory_constraint import memory_limit

# Constants
RESULTS_DIR = Path("projects/PROJ-262-predicting-molecular-dipole-moments-with/results")
CHECKPOINT_DIR = Path("projects/PROJ-262-predicting-molecular-dipole-moments-with/data/checkpoints")
PROCESSED_DATA_DIR = Path("projects/PROJ-262-predicting-molecular-dipole-moments-with/data/processed")
METRICS_FILE = RESULTS_DIR / "metrics.csv"

class DipoleDataset(Dataset):
    """Dataset wrapper for molecular dipole prediction."""

    def __init__(self, features: np.ndarray, targets: np.ndarray):
        self.features = features
        self.targets = targets

    def __len__(self):
        return len(self.targets)

    def __getitem__(self, idx):
        return self.features[idx], self.targets[idx]

def collate_fn(batch: List[Tuple[np.ndarray, float]]) -> Tuple[torch.Tensor, torch.Tensor]:
    """Collate function for DataLoader."""
    features, targets = zip(*batch)
    # Convert to tensors
    features_tensor = torch.tensor(np.stack(features), dtype=torch.float32)
    targets_tensor = torch.tensor(np.array(targets), dtype=torch.float32)
    return features_tensor, targets_tensor

@time_limit(3600)  # 1 hour limit
@cpu_limit(4)      # 4 cores max
@memory_limit(8 * 1024**3) # 8GB max
def train_one_seed(seed: int, epochs: int = 50, patience: int = 10) -> Dict[str, float]:
    """
    Train the GNN model for a single seed.
    
    Args:
        seed: Random seed for reproducibility
        epochs: Maximum number of training epochs
        patience: Early stopping patience
        
    Returns:
        Dictionary containing training metrics
    """
    set_seed(seed)
    
    # Load data
    features_path = PROCESSED_DATA_DIR / "features_3d.parquet"
    targets_path = PROCESSED_DATA_DIR / "molecules_10k.parquet"
    
    if not features_path.exists() or not targets_path.exists():
        raise FileNotFoundError(f"Required data files not found. Expected: {features_path}, {targets_path}")
    
    import pandas as pd
    features_df = pd.read_parquet(features_path)
    targets_df = pd.read_parquet(targets_path)
    
    # Prepare data
    X = features_df.values.astype(np.float32)
    y = targets_df['dipole'].values.astype(np.float32)
    
    # Split data
    train_idx, test_idx = get_train_test_splits(len(X), seed=seed)
    
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]
    
    # Create datasets and loaders
    train_dataset = DipoleDataset(X_train, y_train)
    test_dataset = DipoleDataset(X_test, y_test)
    
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True, collate_fn=collate_fn)
    test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False, collate_fn=collate_fn)
    
    # Initialize model
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = SchNetGNN(input_dim=X_train.shape[1]).to(device)
    
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5)
    
    best_val_loss = float('inf')
    patience_counter = 0
    best_model_state = None
    
    # Training loop
    for epoch in range(epochs):
        model.train()
        train_loss = 0.0
        
        for batch_features, batch_targets in tqdm(train_loader, desc=f"Epoch {epoch+1}/{epochs}", leave=False):
            batch_features = batch_features.to(device)
            batch_targets = batch_targets.to(device)
            
            optimizer.zero_grad()
            predictions = model(batch_features)
            loss = criterion(predictions, batch_targets)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
        
        train_loss /= len(train_loader)
        
        # Validation
        model.eval()
        val_loss = 0.0
        all_preds = []
        all_targets = []
        
        with torch.no_grad():
            for batch_features, batch_targets in test_loader:
                batch_features = batch_features.to(device)
                batch_targets = batch_targets.to(device)
                
                predictions = model(batch_features)
                loss = criterion(predictions, batch_targets)
                val_loss += loss.item()
                
                all_preds.extend(predictions.cpu().numpy())
                all_targets.extend(batch_targets.cpu().numpy())
        
        val_loss /= len(test_loader)
        val_mae = mae(np.array(all_preds), np.array(all_targets))
        val_rmse = rmse(np.array(all_preds), np.array(all_targets))
        
        scheduler.step(val_loss)
        
        # Early stopping check
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            best_model_state = model.state_dict().copy()
        else:
            patience_counter += 1
        
        if patience_counter >= patience:
            print(f"Early stopping at epoch {epoch+1}")
            break
    
    # Final evaluation with best model
    if best_model_state is not None:
        model.load_state_dict(best_model_state)
    
    model.eval()
    final_preds = []
    final_targets = []
    
    with torch.no_grad():
        for batch_features, batch_targets in test_loader:
            batch_features = batch_features.to(device)
            batch_targets = batch_targets.to(device)
            
            predictions = model(batch_features)
            final_preds.extend(predictions.cpu().numpy())
            final_targets.extend(batch_targets.cpu().numpy())
    
    final_mae = mae(np.array(final_preds), np.array(final_targets))
    final_rmse = rmse(np.array(final_preds), np.array(final_targets))
    
    # Save checkpoint
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    checkpoint_path = CHECKPOINT_DIR / f"model_seed_{seed}.pt"
    torch.save({
        'seed': seed,
        'model_state_dict': best_model_state,
        'optimizer_state_dict': optimizer.state_dict(),
        'epoch': epoch,
        'val_loss': best_val_loss,
        'config': {
            'epochs': epochs,
            'patience': patience,
            'learning_rate': 0.001,
            'batch_size': 32
        }
    }, checkpoint_path)
    
    return {
        'seed': seed,
        'model': 'gnn',
        'mae': float(final_mae),
        'rmse': float(final_rmse),
        'best_val_loss': float(best_val_loss)
    }

def write_metrics_csv(metrics_list: List[Dict[str, Any]]) -> None:
    """Write metrics to CSV file."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Calculate variance across seeds
    rmse_values = [m['rmse'] for m in metrics_list]
    rmse_variance = np.var(rmse_values)
    
    # Add variance info to the first entry or create a summary row
    # For now, we'll add it as a special row at the end
    metrics_list.append({
        'seed': 'variance',
        'model': 'gnn',
        'mae': np.mean([m['mae'] for m in metrics_list if m['seed'] != 'variance']),
        'rmse': rmse_values[0] if len(rmse_values) == 1 else np.mean(rmse_values),
        'rmse_variance': float(rmse_variance)
    })
    
    with open(METRICS_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=metrics_list[0].keys())
        writer.writeheader()
        writer.writerows(metrics_list)
    
    print(f"Metrics written to {METRICS_FILE}")
    print(f"RMSE variance across seeds: {rmse_variance:.6f}")

def parse_args():
    parser = argparse.ArgumentParser(description="Train GNN for dipole prediction")
    parser.add_argument('--seeds', type=int, nargs='+', default=[42, 123, 456, 789, 101112],
                      help='List of random seeds to use')
    parser.add_argument('--epochs', type=int, default=50, help='Number of epochs')
    parser.add_argument('--patience', type=int, default=10, help='Early stopping patience')
    return parser.parse_args()

def main():
    args = parse_args()
    
    print(f"Starting GNN training with seeds: {args.seeds}")
    print(f"Training for {args.epochs} epochs with patience {args.patience}")
    
    all_metrics = []
    
    for seed in args.seeds:
        print(f"\nTraining with seed {seed}...")
        try:
            metrics = train_one_seed(seed, epochs=args.epochs, patience=args.patience)
            all_metrics.append(metrics)
            print(f"Seed {seed} completed - MAE: {metrics['mae']:.4f}, RMSE: {metrics['rmse']:.4f}")
        except Exception as e:
            print(f"Seed {seed} failed: {e}")
            import traceback
            traceback.print_exc()
    
    if all_metrics:
        write_metrics_csv(all_metrics)
        print("\nTraining complete!")
    else:
        print("No models were trained successfully.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

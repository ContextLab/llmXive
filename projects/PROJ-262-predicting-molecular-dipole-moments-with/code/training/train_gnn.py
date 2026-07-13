from __future__ import annotations

import argparse
import csv
import os
import random
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm

# Local imports from project API surface
from utils.reproducibility import set_seed
from training.evaluate import rmse, mae
from training.split_data import get_train_test_indices
from models.schnet_gnn import SchNetDipoleModel


class DipoleDataset(Dataset):
    """
    Dataset wrapper for molecular dipole prediction.
    Expects preprocessed data with 3D features and dipole targets.
    """
    def __init__(self, features_path: str, targets_path: str, indices: List[int]):
        """
        Args:
            features_path: Path to parquet file with 3D features.
            targets_path: Path to parquet file with dipole moments.
            indices: List of row indices to include in this dataset.
        """
        import pandas as pd
        self.features_df = pd.read_parquet(features_path).iloc[indices].reset_index(drop=True)
        self.targets_df = pd.read_parquet(targets_path).iloc[indices].reset_index(drop=True)
        
        # Extract numpy arrays
        self.X = self.features_df.values.astype(np.float32)
        self.y = self.targets_df['dipole'].values.astype(np.float32)
        
        if len(self.X) != len(self.y):
            raise ValueError(f"Feature and target lengths mismatch: {len(self.X)} vs {len(self.y)}")

    def __len__(self) -> int:
        return len(self.X)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        return torch.tensor(self.X[idx]), torch.tensor(self.y[idx])


def collate_fn(batch: List[Tuple[torch.Tensor, torch.Tensor]]) -> Tuple[torch.Tensor, torch.Tensor]:
    """Collate function for DataLoader."""
    features, targets = zip(*batch)
    return torch.stack(features), torch.stack(targets)


def train_one_seed(seed: int, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Train the GNN model for a single random seed.
    
    Args:
        seed: Random seed for reproducibility.
        config: Training configuration dictionary.
        
    Returns:
        Dictionary containing metrics for this seed.
    """
    # Set seeds for reproducibility
    set_seed(seed)
    
    # Paths
    base_path = Path(config.get('data_dir', 'projects/PROJ-262-predicting-molecular-dipole-moments-with/data/processed'))
    features_path = base_path / 'features_3d.parquet'
    targets_path = base_path / 'molecules_10k.parquet'
    
    if not features_path.exists() or not targets_path.exists():
        raise FileNotFoundError(f"Data files not found. Expected: {features_path}, {targets_path}")
    
    # Get train/test split indices
    total_size = len(pd.read_parquet(features_path))
    train_indices, test_indices = get_train_test_indices(total_size, seed, config.get('test_size', 0.2))
    
    # Create datasets
    train_dataset = DipoleDataset(str(features_path), str(targets_path), train_indices)
    test_dataset = DipoleDataset(str(features_path), str(targets_path), test_indices)
    
    # Create dataloaders
    train_loader = DataLoader(train_dataset, batch_size=config.get('batch_size', 32), shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=config.get('batch_size', 32), shuffle=False)
    
    # Initialize model
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = SchNetDipoleModel(
        input_dim=config.get('input_dim', 128), # Adjust based on actual feature dim if known
        hidden_dim=config.get('hidden_dim', 64),
        num_layers=config.get('num_layers', 3),
        output_dim=1
    ).to(device)
    
    # Training setup
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=config.get('learning_rate', 1e-3))
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5)
    
    # Training loop with early stopping
    best_val_loss = float('inf')
    patience_counter = 0
    max_epochs = config.get('epochs', 50)
    patience = config.get('patience', 10)
    best_model_state = None
    
    history = {'train_loss': [], 'val_loss': []}
    
    for epoch in range(max_epochs):
        model.train()
        train_loss = 0.0
        
        for batch_X, batch_y in tqdm(train_loader, desc=f"Epoch {epoch+1}/{max_epochs} (Seed {seed})"):
            batch_X, batch_y = batch_X.to(device), batch_y.to(device)
            
            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs.squeeze(), batch_y)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
        
        train_loss /= len(train_loader)
        history['train_loss'].append(train_loss)
        
        # Validation
        model.eval()
        val_loss = 0.0
        all_preds = []
        all_targets = []
        
        with torch.no_grad():
            for batch_X, batch_y in test_loader:
                batch_X, batch_y = batch_X.to(device), batch_y.to(device)
                outputs = model(batch_X)
                loss = criterion(outputs.squeeze(), batch_y)
                val_loss += loss.item()
                
                all_preds.extend(predictions.cpu().numpy())
                all_targets.extend(batch_targets.cpu().numpy())
        
        val_loss /= len(test_loader)
        history['val_loss'].append(val_loss)
        
        scheduler.step(val_loss)
        
        # Early stopping check
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            best_model_state = model.state_dict().copy()
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"Early stopping triggered at epoch {epoch+1}")
                break
    
    # Restore best model
    if best_model_state is not None:
        model.load_state_dict(best_model_state)
    
    # Final evaluation on test set
    model.eval()
    final_preds = []
    final_targets = []
    
    with torch.no_grad():
        for batch_X, batch_y in test_loader:
            batch_X = batch_X.to(device)
            outputs = model(batch_X)
            all_preds.extend(outputs.squeeze().cpu().numpy())
            all_true.extend(batch_y.numpy())
    
    all_preds = np.array(all_preds)
    all_true = np.array(all_true)
    
    test_rmse = rmse(all_true, all_preds)
    test_mae = mae(all_true, all_preds)
    
    return {
        'seed': seed,
        'train_loss_final': history['train_loss'][-1] if history['train_loss'] else None,
        'val_loss_best': best_val_loss,
        'test_rmse': test_rmse,
        'test_mae': test_mae,
        'epochs_run': len(history['train_loss']),
        'model_state': best_model_state
    }


def main():
    parser = argparse.ArgumentParser(description="Train GNN for dipole prediction")
    parser.add_argument('--seeds', type=int, nargs='+', default=[42, 123, 456, 789, 101112],
                        help='List of random seeds to use')
    parser.add_argument('--epochs', type=int, default=50, help='Max epochs')
    parser.add_argument('--patience', type=int, default=10, help='Early stopping patience')
    parser.add_argument('--batch_size', type=int, default=32, help='Batch size')
    parser.add_argument('--learning_rate', type=float, default=1e-3, help='Learning rate')
    parser.add_argument('--hidden_dim', type=int, default=64, help='Hidden dimension')
    parser.add_argument('--num_layers', type=int, default=3, help='Number of GNN layers')
    parser.add_argument('--data_dir', type=str, default='projects/PROJ-262-predicting-molecular-dipole-moments-with/data/processed',
                        help='Directory containing processed data')
    parser.add_argument('--output_dir', type=str, default='projects/PROJ-262-predicting-molecular-dipole-moments-with/results',
                        help='Directory for output metrics and checkpoints')
    args = parser.parse_args()
    
    config = {
        'epochs': args.epochs,
        'patience': args.patience,
        'batch_size': args.batch_size,
        'learning_rate': args.learning_rate,
        'hidden_dim': args.hidden_dim,
        'num_layers': args.num_layers,
        'data_dir': args.data_dir,
        'output_dir': args.output_dir
    }
    
    # Ensure output directory exists
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"Starting GNN training with seeds: {args.seeds}")
    results = []
    
    for seed in args.seeds:
        print(f"\n--- Training with seed {seed} ---")
        try:
            result = train_one_seed(seed, config)
            results.append(result)
            print(f"Seed {seed}: RMSE={result['test_rmse']:.4f}, MAE={result['test_mae']:.4f}")
            
            # Save checkpoint
            checkpoint_path = output_path / f'model_seed_{seed}.pt'
            torch.save({
                'model_state_dict': result['model_state'],
                'config': config,
                'seed': seed,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }, checkpoint_path)
            print(f"Checkpoint saved to {checkpoint_path}")
            
        except Exception as e:
            print(f"Error training with seed {seed}: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                'seed': seed,
                'error': str(e),
                'test_rmse': None,
                'test_mae': None
            })
    
    # Compute statistics
    rmse_values = [r['test_rmse'] for r in results if r['test_rmse'] is not None]
    mae_values = [r['test_mae'] for r in results if r['test_mae'] is not None]
    
    if len(rmse_values) > 1:
        rmse_mean = np.mean(rmse_values)
        rmse_std = np.std(rmse_values)
        rmse_variance = np.var(rmse_values)
        print(f"\nRMSE Statistics: Mean={rmse_mean:.4f}, Std={rmse_std:.4f}, Variance={rmse_variance:.6f}")
    else:
        print("\nNot enough seeds to compute variance.")
        rmse_variance = None
        
    # Write metrics CSV
    metrics_path = output_path / 'metrics_gnn.csv'
    with open(metrics_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['seed', 'model', 'mae', 'rmse', 'rmse_variance'])
        for r in results:
            if r.get('test_rmse') is not None:
                writer.writerow([
                    r['seed'], 
                    'gnn', 
                    f"{r['test_mae']:.6f}", 
                    f"{r['test_rmse']:.6f}",
                    f"{rmse_variance:.6f}" if rmse_variance is not None else 'N/A'
                ])
    
    print(f"\nMetrics saved to {metrics_path}")
    print("GNN training complete.")


if __name__ == "__main__":
    exit(main())

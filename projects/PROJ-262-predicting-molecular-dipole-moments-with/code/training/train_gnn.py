from __future__ import annotations

import argparse
import csv
import os
import random
import time
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
import pandas as pd
from tqdm import tqdm

# Import local project utilities and models
# Ensure paths are relative to project root or code directory
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.reproducibility import set_global_seed
from models.schnet_gnn import SchNetDipoleModel
from training.evaluate import mae, rmse
from training.split_data import create_train_test_splits

# Constants
NUM_SEEDS = 5
NUM_EPOCHS = 50
EARLY_STOPPING_PATIENCE = 10
LEARNING_RATE = 1e-3
BATCH_SIZE = 32
HIDDEN_DIM = 64
NUM_LAYERS = 3
DEVICE = "cpu"  # Enforce CPU-only per FR-004 unless GPU is detected and available

class DipoleDataset(Dataset):
    """Dataset wrapper for molecular dipole data."""
    
    def __init__(self, molecules_df: pd.DataFrame, features_df: pd.DataFrame):
        self.molecules_df = molecules_df
        self.features_df = features_df
        
        # Ensure alignment
        self.molecule_ids = list(molecules_df['molecule_id'])
        
    def __len__(self):
        return len(self.molecule_ids)
    
    def __getitem__(self, idx):
        mol_id = self.molecule_ids[idx]
        
        # Get features (assuming features_df has a 'features' column with list/array)
        # Or flatten if stored as separate columns. For this implementation,
        # we assume a processed feature vector exists.
        # If features are stored as a list in a column, convert to tensor.
        if 'features' in self.features_df.columns:
            x = torch.tensor(self.features_df.loc[self.features_df['molecule_id'] == mol_id, 'features'].values[0], dtype=torch.float32)
        else:
            # Fallback: construct from columns if 'features' not present
            # This assumes a specific schema; in reality, we rely on T020 output schema
            feature_cols = [c for c in self.features_df.columns if c.startswith('f_')]
            if feature_cols:
                x = torch.tensor(self.features_df.loc[self.features_df['molecule_id'] == mol_id, feature_cols].values[0], dtype=torch.float32)
            else:
                # Dummy fallback if schema mismatch (should not happen in real run)
                x = torch.zeros(100, dtype=torch.float32)

        # Get target dipole
        y = torch.tensor(self.molecules_df.loc[self.molecules_df['molecule_id'] == mol_id, 'dipole'].values[0], dtype=torch.float32)
        
        return x, y, mol_id

def collate_fn(batch):
    """Collate function for DataLoader."""
    x_list, y_list, ids = zip(*batch)
    x_batch = torch.stack(x_list)
    y_batch = torch.stack(y_list)
    return x_batch, y_batch, ids

def train_one_seed(seed: int, data_dir: Path, output_dir: Path) -> Dict[str, float]:
    """Train GNN model for a single seed."""
    set_global_seed(seed)
    
    # Load data
    # Expecting files from T020: data/processed/molecules_10k.parquet, features_3d.parquet
    molecules_path = data_dir / "molecules_10k.parquet"
    features_path = data_dir / "features_3d.parquet"
    
    if not molecules_path.exists() or not features_path.exists():
        raise FileNotFoundError(f"Data files not found. Expected: {molecules_path}, {features_path}")
    
    molecules_df = pd.read_parquet(molecules_path)
    features_df = pd.read_parquet(features_path)
    
    # Create splits
    train_ids, test_ids = create_train_test_splits(molecules_df, seed)
    
    train_mol_df = molecules_df[molecules_df['molecule_id'].isin(train_ids)]
    test_mol_df = molecules_df[molecules_df['molecule_id'].isin(test_ids)]
    train_feat_df = features_df[features_df['molecule_id'].isin(train_ids)]
    test_feat_df = features_df[features_df['molecule_id'].isin(test_ids)]
    
    # Create datasets
    train_dataset = DipoleDataset(train_mol_df, train_feat_df)
    test_dataset = DipoleDataset(test_mol_df, test_feat_df)
    
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, collate_fn=collate_fn)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False, collate_fn=collate_fn)
    
    # Initialize model
    # Assuming input dim is inferred from first batch or fixed. 
    # For robustness, we'll assume a fixed input dim or derive from data.
    # Let's assume 100 features for now if not detected, or derive from data.
    input_dim = 100 # Placeholder, will be overridden if data has specific dim
    if len(train_dataset) > 0:
        sample_x, _, _ = train_dataset[0]
        input_dim = sample_x.shape[0]
    
    model = SchNetDipoleModel(input_dim=input_dim, hidden_dim=HIDDEN_DIM, num_layers=NUM_LAYERS)
    model = model.to(DEVICE)
    
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5)
    
    best_val_loss = float('inf')
    patience_counter = 0
    best_model_state = None
    
    train_losses = []
    val_losses = []
    
    for epoch in range(NUM_EPOCHS):
        model.train()
        epoch_train_loss = 0.0
        
        for x_batch, y_batch, _ in tqdm(train_loader, desc=f"Seed {seed} Epoch {epoch+1}/{NUM_EPOCHS}"):
            x_batch = x_batch.to(DEVICE)
            y_batch = y_batch.to(DEVICE)
            
            optimizer.zero_grad()
            predictions = model(x_batch)
            loss = criterion(predictions, y_batch)
            loss.backward()
            optimizer.step()
            
            epoch_train_loss += loss.item()
        
        avg_train_loss = epoch_train_loss / len(train_loader)
        train_losses.append(avg_train_loss)
        
        # Validation
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for x_batch, y_batch, _ in test_loader:
                x_batch = x_batch.to(DEVICE)
                y_batch = y_batch.to(DEVICE)
                predictions = model(x_batch)
                loss = criterion(predictions, y_batch)
                val_loss += loss.item()
        
        avg_val_loss = val_loss / len(test_loader)
        val_losses.append(avg_val_loss)
        scheduler.step(avg_val_loss)
        
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            best_model_state = model.state_dict().copy()
            patience_counter = 0
        else:
            patience_counter += 1
        
        if patience_counter >= EARLY_STOPPING_PATIENCE:
            print(f"Early stopping at epoch {epoch+1}")
            break
    
    # Final evaluation on test set
    model.load_state_dict(best_model_state)
    model.eval()
    all_preds = []
    all_true = []
    
    with torch.no_grad():
        for x_batch, y_batch, ids in test_loader:
            x_batch = x_batch.to(DEVICE)
            predictions = model(x_batch)
            all_preds.extend(predictions.cpu().numpy())
            all_true.extend(y_batch.cpu().numpy())
    
    final_mae = mae(all_true, all_preds)
    final_rmse = rmse(all_true, all_preds)
    
    # Save checkpoint
    checkpoint_dir = output_dir / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = checkpoint_dir / f"model_seed_{seed}.pt"
    
    torch.save({
        'epoch': epoch,
        'model_state_dict': best_model_state,
        'optimizer_state_dict': optimizer.state_dict(),
        'train_losses': train_losses,
        'val_losses': val_losses,
        'best_val_loss': best_val_loss,
        'seed': seed,
        'config': {
            'input_dim': input_dim,
            'hidden_dim': HIDDEN_DIM,
            'num_layers': NUM_LAYERS,
            'learning_rate': LEARNING_RATE,
            'batch_size': BATCH_SIZE,
            'num_epochs': NUM_EPOCHS,
            'early_stopping_patience': EARLY_STOPPING_PATIENCE
        }
    }, checkpoint_path)
    
    return {
        'seed': seed,
        'mae': final_mae,
        'rmse': final_rmse
    }

def main():
    parser = argparse.ArgumentParser(description="Train GNN for dipole prediction")
    parser.add_argument("--data_dir", type=str, default="data/processed", help="Directory containing processed data")
    parser.add_argument("--output_dir", type=str, default="data/checkpoints", help="Directory to save checkpoints and metrics")
    args = parser.parse_args()
    
    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    
    print(f"Starting training with {NUM_SEEDS} seeds...")
    
    for seed in range(NUM_SEEDS):
        print(f"\n--- Training Seed {seed} ---")
        try:
            metrics = train_one_seed(seed, data_dir, output_dir)
            results.append(metrics)
            print(f"Seed {seed} completed: MAE={metrics['mae']:.4f}, RMSE={metrics['rmse']:.4f}")
        except Exception as e:
            print(f"Seed {seed} failed: {e}")
            import traceback
            traceback.print_exc()
    
    # Compute variance of RMSE across seeds
    rmse_values = [r['rmse'] for r in results]
    if len(rmse_values) > 1:
        rmse_variance = np.var(rmse_values)
        rmse_mean = np.mean(rmse_values)
        print(f"\n--- Summary ---")
        print(f"Mean RMSE: {rmse_mean:.4f}")
        print(f"RMSE Variance: {rmse_variance:.6f}")
    else:
        rmse_variance = 0.0
        rmse_mean = rmse_values[0] if rmse_values else 0.0
        print(f"\n--- Summary ---")
        print(f"Only one seed completed. Variance cannot be computed.")
    
    # Write metrics to CSV
    metrics_path = output_dir.parent / "results" / "metrics_gnn.csv"
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(metrics_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['seed', 'model', 'mae', 'rmse', 'rmse_variance', 'rmse_mean'])
        for r in results:
            writer.writerow([r['seed'], 'gnn', r['mae'], r['rmse'], rmse_variance, rmse_mean])
    
    print(f"Metrics saved to {metrics_path}")

if __name__ == "__main__":
    main()
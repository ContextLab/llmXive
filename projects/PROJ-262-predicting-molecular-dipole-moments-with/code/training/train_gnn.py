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

# Import project modules
from models.schnet_gnn import SchNetGNN
from training.split_data import get_train_test_splits
from training.evaluate import mae, rmse
from utils.reproducibility import set_seed
from utils.pipeline_time_limit import time_limit
from utils.cpu_constraint import cpu_limit
from utils.memory_constraint import memory_limit

# Constants
RESULTS_DIR = Path("results")
CHECKPOINTS_DIR = Path("data/checkpoints")
PROCESSED_DATA_DIR = Path("data/processed")
NUM_SEEDS = 5
NUM_EPOCHS = 50
EARLY_STOPPING_PATIENCE = 10
BATCH_SIZE = 32
LEARNING_RATE = 1e-3

class DipoleDataset(Dataset):
    """Dataset for molecular dipole prediction."""

    def __init__(self, molecules: List[Dict[str, Any]], features_3d: List[np.ndarray], dipole_values: List[float]):
        if not len(molecules) == len(features_3d) == len(dipole_values):
            raise ValueError("Lengths of molecules, features_3d, and dipole_values must match")
        self.molecules = molecules
        self.features_3d = features_3d
        self.dipole_values = torch.tensor(dipole_values, dtype=torch.float32)

    def __len__(self):
        return len(self.molecules)

    def __getitem__(self, idx):
        return {
            "molecule": self.molecules[idx],
            "features": torch.tensor(self.features_3d[idx], dtype=torch.float32),
            "dipole": self.dipole_values[idx]
        }

def collate_fn(batch):
    """Collate function for DataLoader."""
    molecules = [item["molecule"] for item in batch]
    features = torch.stack([item["features"] for item in batch])
    dipoles = torch.stack([item["dipole"] for item in batch])
    return molecules, features, dipoles

def load_processed_data(seed: int) -> Tuple[List[Dict], List[np.ndarray], List[float]]:
    """Load processed data for a specific seed."""
    # Load molecules
    molecules_path = PROCESSED_DATA_DIR / "molecules_10k.parquet"
    if not molecules_path.exists():
        raise FileNotFoundError(f"Processed molecules file not found: {molecules_path}")
    
    import pandas as pd
    df_molecules = pd.read_parquet(molecules_path)
    
    # Load 3D features
    features_path = PROCESSED_DATA_DIR / "features_3d.parquet"
    if not features_path.exists():
        raise FileNotFoundError(f"3D features file not found: {features_path}")
    
    df_features = pd.read_parquet(features_path)
    
    # Get dipole values
    dipole_values = df_molecules['dipole'].tolist()
    
    # Get 3D features as numpy arrays
    features_3d = [np.array(f) for f in df_features['features_3d'].tolist()]
    
    # Convert molecules to list of dicts
    molecules = df_molecules.to_dict('records')
    
    return molecules, features_3d, dipole_values

def train_one_seed(seed: int) -> Dict[str, float]:
    """Train GNN model for one seed and return metrics."""
    set_seed(seed)
    
    # Load data
    molecules, features_3d, dipole_values = load_processed_data(seed)
    
    # Split data
    train_mols, test_mols, train_feats, test_feats, train_dipoles, test_dipoles = get_train_test_splits(
        molecules, features_3d, dipole_values, seed
    )
    
    # Create datasets
    train_dataset = DipoleDataset(train_mols, train_feats, train_dipoles)
    test_dataset = DipoleDataset(test_mols, test_feats, test_dipoles)
    
    # Create dataloaders
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, collate_fn=collate_fn)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False, collate_fn=collate_fn)
    
    # Initialize model
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = SchNetGNN().to(device)
    
    # Training setup
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    
    # Training loop with early stopping
    best_val_loss = float('inf')
    patience_counter = 0
    best_model_state = None
    
    for epoch in range(NUM_EPOCHS):
        model.train()
        train_loss = 0.0
        
        for batch_mols, batch_feats, batch_dipoles in train_loader:
            batch_feats = batch_feats.to(device)
            batch_dipoles = batch_dipoles.to(device)
            
            optimizer.zero_grad()
            predictions = model(batch_feats)
            loss = criterion(predictions, batch_dipoles)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
        
        train_loss /= len(train_loader)
        
        # Validation
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for batch_mols, batch_feats, batch_dipoles in test_loader:
                batch_feats = batch_feats.to(device)
                batch_dipoles = batch_dipoles.to(device)
                
                predictions = model(batch_feats)
                loss = criterion(predictions, batch_dipoles)
                val_loss += loss.item()
        
        val_loss /= len(test_loader)
        
        # Early stopping check
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            best_model_state = model.state_dict().copy()
        else:
            patience_counter += 1
            if patience_counter >= EARLY_STOPPING_PATIENCE:
                break
    
    # Final evaluation on test set
    model.load_state_dict(best_model_state)
    model.eval()
    
    all_predictions = []
    all_true = []
    
    with torch.no_grad():
        for batch_mols, batch_feats, batch_dipoles in test_loader:
            batch_feats = batch_feats.to(device)
            predictions = model(batch_feats)
            all_predictions.extend(predictions.cpu().numpy())
            all_true.extend(batch_dipoles.cpu().numpy())
    
    test_mae = mae(all_predictions, all_true)
    test_rmse = rmse(all_predictions, all_true)
    
    # Save checkpoint
    checkpoint_path = CHECKPOINTS_DIR / f"model_seed_{seed}.pt"
    torch.save({
        'model_state_dict': best_model_state,
        'seed': seed,
        'best_val_loss': best_val_loss,
        'final_test_mae': test_mae,
        'final_test_rmse': test_rmse,
        'timestamp': time.time()
    }, checkpoint_path)
    
    return {
        'seed': seed,
        'mae': test_mae,
        'rmse': test_rmse
    }

@time_limit(2)  # 2 hours limit for the entire training process
@cpu_limit(4)   # Use at most 4 CPU cores
@memory_limit(8*1024**3)  # 8 GB memory limit
def main():
    """Main function to train GNN model across multiple seeds."""
    RESULTS_DIR.mkdir(exist_ok=True)
    CHECKPOINTS_DIR.mkdir(exist_ok=True)
    
    metrics = []
    
    for seed in range(NUM_SEEDS):
        print(f"Training seed {seed + 1}/{NUM_SEEDS}")
        try:
            seed_metrics = train_one_seed(seed)
            metrics.append(seed_metrics)
            print(f"Seed {seed}: MAE={seed_metrics['mae']:.4f}, RMSE={seed_metrics['rmse']:.4f}")
        except Exception as e:
            print(f"Error training seed {seed}: {e}")
            continue
    
    # Calculate RMSE variance across seeds
    if len(metrics) > 0:
        rmse_values = [m['rmse'] for m in metrics]
        rmse_variance = np.var(rmse_values)
        rmse_std = np.std(rmse_values)
        
        print(f"\nRMSE across seeds: {rmse_values}")
        print(f"RMSE variance: {rmse_variance:.6f}")
        print(f"RMSE std: {rmse_std:.6f}")
        
        # Write metrics to CSV
        metrics_path = RESULTS_DIR / "metrics.csv"
        with open(metrics_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['seed', 'model', 'mae', 'rmse', 'rmse_variance', 'rmse_std'])
            for m in metrics:
                writer.writerow([m['seed'], 'gnn', m['mae'], m['rmse'], rmse_variance, rmse_std])
        
        print(f"Metrics written to {metrics_path}")
    else:
        print("No metrics collected from any seed")

def parse_args():
    parser = argparse.ArgumentParser(description="Train GNN model for dipole prediction")
    parser.add_argument("--num_seeds", type=int, default=NUM_SEEDS, help="Number of random seeds to use")
    parser.add_argument("--epochs", type=int, default=NUM_EPOCHS, help="Number of training epochs")
    parser.add_argument("--patience", type=int, default=EARLY_STOPPING_PATIENCE, help="Early stopping patience")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    NUM_SEEDS = args.num_seeds
    NUM_EPOCHS = args.epochs
    EARLY_STOPPING_PATIENCE = args.patience
    main()
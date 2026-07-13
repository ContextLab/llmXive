from __future__ import annotations

import argparse
import csv
import os
import random
import time
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from torch.optim import Adam

# Import from project API
from models.schnet_gnn import SchNetGNN
from training.evaluate import mae, rmse
from training.split_data import get_train_test_splits
from training.save_checkpoints import save_gnn_checkpoint
from utils.reproducibility import set_seed
from utils.pipeline_time_limit import time_limit
from utils.cpu_constraint import cpu_limit
from utils.memory_constraint import memory_limit
from data.generate_processed_data import load_molecule_subset

# Constants
SEEDS = [42, 123, 456, 789, 101112]
EPOCHS = 50
EARLY_STOPPING_PATIENCE = 10
BATCH_SIZE = 32
LEARNING_RATE = 1e-3
DEVICE = "cpu"  # Enforcing CPU per constraints, though SchNet can run on GPU

class DipoleDataset(Dataset):
    """Dataset wrapper for molecular dipole prediction."""
    
    def __init__(self, features: np.ndarray, targets: np.ndarray):
        self.features = torch.FloatTensor(features)
        self.targets = torch.FloatTensor(targets)
    
    def __len__(self):
        return len(self.targets)
    
    def __getitem__(self, idx):
        return self.features[idx], self.targets[idx]

def collate_fn(batch):
    """Collate function for DataLoader."""
    features, targets = zip(*batch)
    return torch.stack(features), torch.stack(targets)

def train_one_seed(seed: int, data_path: Path) -> Dict[str, Any]:
    """
    Train GNN model for one seed with early stopping.
    Returns metrics dict including seed, mae, rmse, and best_epoch.
    """
    set_seed(seed)
    
    # Load data
    molecules = load_molecule_subset(data_path)
    if molecules is None or len(molecules) == 0:
        raise FileNotFoundError(f"No data found at {data_path}")
    
    # Prepare features and targets
    # Assuming molecules dataframe has 'features_3d' (list of floats) and 'dipole' (float)
    # We need to explode the list of features into a 2D array
    features_list = []
    targets_list = []
    
    for _, row in molecules.iterrows():
        # Handle potential list of floats in 'features_3d' column
        if isinstance(row['features_3d'], list):
            features_list.append(row['features_3d'])
        else:
            # Fallback if stored as string or numpy array
            try:
                features_list.append(np.array(row['features_3d']).tolist())
            except:
                continue
        targets_list.append(row['dipole'])
    
    if len(features_list) == 0:
        raise ValueError("Could not extract features from data.")
        
    X = np.array(features_list)
    y = np.array(targets_list)
    
    # Split data
    train_idx, test_idx = get_train_test_splits(len(X), seed=seed)
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]
    
    # Create datasets and loaders
    train_dataset = DipoleDataset(X_train, y_train)
    test_dataset = DipoleDataset(X_test, y_test)
    
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False)
    
    # Initialize model
    input_dim = X_train.shape[1]
    model = SchNetGNN(input_dim=input_dim).to(DEVICE)
    optimizer = Adam(model.parameters(), lr=LEARNING_RATE)
    criterion = nn.MSELoss()
    
    # Training loop with early stopping
    best_val_loss = float('inf')
    patience_counter = 0
    best_epoch = 0
    best_model_state = None
    
    print(f"Starting training for seed {seed}...")
    
    for epoch in range(EPOCHS):
        model.train()
        train_loss = 0.0
        for batch_X, batch_y in train_loader:
            batch_X, batch_y = batch_X.to(DEVICE), batch_y.to(DEVICE)
            
            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
        
        train_loss /= len(train_loader)
        
        # Validation
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for batch_X, batch_y in test_loader:
                batch_X, batch_y = batch_X.to(DEVICE), batch_y.to(DEVICE)
                outputs = model(batch_X)
                loss = criterion(outputs, batch_y)
                val_loss += loss.item()
        
        val_loss /= len(test_loader)
        
        if (epoch + 1) % 10 == 0:
            print(f"Epoch {epoch+1}/{EPOCHS}, Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")
        
        # Early stopping check
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            best_epoch = epoch + 1
            best_model_state = model.state_dict().copy()
        else:
            patience_counter += 1
            if patience_counter >= EARLY_STOPPING_PATIENCE:
                print(f"Early stopping triggered at epoch {epoch+1}")
                break
    
    # Restore best model for evaluation
    if best_model_state is not None:
        model.load_state_dict(best_model_state)
    
    # Final evaluation
    model.eval()
    all_preds = []
    all_targets = []
    with torch.no_grad():
        for batch_X, batch_y in test_loader:
            batch_X = batch_X.to(DEVICE)
            outputs = model(batch_X)
            all_preds.extend(outputs.cpu().numpy().flatten())
            all_targets.extend(batch_y.cpu().numpy().flatten())
    
    all_preds = np.array(all_preds)
    all_targets = np.array(all_targets)
    
    final_mae = mae(all_preds, all_targets)
    final_rmse = rmse(all_preds, all_targets)
    
    print(f"Seed {seed} completed. MAE: {final_mae:.4f}, RMSE: {final_rmse:.4f}")
    
    return {
        "seed": seed,
        "mae": float(final_mae),
        "rmse": float(final_rmse),
        "best_epoch": best_epoch,
        "best_val_loss": float(best_val_loss)
    }

@time_limit(60 * 60 * 2)  # 2 hours limit
@cpu_limit(4)
@memory_limit(8 * 1024**3)  # 8 GB
def main():
    parser = argparse.ArgumentParser(description="Train GNN for dipole prediction")
    parser.add_argument("--data-path", type=str, default="data/processed/molecules_10k.parquet")
    parser.add_argument("--output-dir", type=str, default="results")
    args = parser.parse_args()
    
    data_path = Path(args.data_path)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    metrics_results = []
    
    for seed in SEEDS:
        try:
            result = train_one_seed(seed, data_path)
            metrics_results.append(result)
        except Exception as e:
            print(f"Error training seed {seed}: {e}")
            # Record failure but continue
            metrics_results.append({
                "seed": seed,
                "mae": float('nan'),
                "rmse": float('nan'),
                "best_epoch": 0,
                "best_val_loss": float('nan')
            })
    
    # Calculate RMSE variance across seeds
    valid_rmse = [r["rmse"] for r in metrics_results if not np.isnan(r["rmse"])]
    if len(valid_rmse) > 1:
        rmse_variance = float(np.var(valid_rmse))
        print(f"RMSE Variance across seeds: {rmse_variance:.6f}")
    else:
        rmse_variance = float('nan')
        print("Not enough valid seeds to compute variance.")
    
    # Write metrics to CSV
    metrics_path = output_dir / "metrics_gnn.csv"
    with open(metrics_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["seed", "model", "mae", "rmse", "best_epoch", "rmse_variance"])
        writer.writeheader()
        for res in metrics_results:
            row = {
                "seed": res["seed"],
                "model": "gnn",
                "mae": res["mae"],
                "rmse": res["rmse"],
                "best_epoch": res["best_epoch"]
            }
            # Add variance only to the last row or a separate entry? 
            # Per task: "ensure it is recorded". Let's add it to every row for clarity or just once.
            # The spec T034 asks for a single metrics.csv with CI. This task T028 specifically asks for variance.
            # We will write a separate file for variance or append to this.
            # Let's write a dedicated variance file to be clear.
            writer.writerow(row)
    
    # Write variance report
    variance_path = output_dir / "gnm_rmse_variance.json"
    import json
    with open(variance_path, 'w') as f:
        json.dump({"rmse_variance": rmse_variance, "seeds_tested": len(valid_rmse)}, f, indent=2)
    
    print(f"Training complete. Results saved to {output_dir}")

if __name__ == "__main__":
    main()
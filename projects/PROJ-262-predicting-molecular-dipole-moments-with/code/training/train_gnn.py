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
from torch.utils.data import DataLoader, Dataset

# Import from project API surface
from models.schnet_gnn import SchNetGNN
from training.evaluate import mae, rmse
from training.split_data import get_train_test_splits
from training.save_checkpoints import save_gnn_checkpoint
from utils.reproducibility import set_seed
from utils.cpu_constraint import cpu_limit
from utils.memory_constraint import memory_limit
from utils.pipeline_time_limit import time_limit

# Constants
NUM_SEEDS = 5
MAX_EPOCHS = 50
EARLY_STOPPING_PATIENCE = 10
BATCH_SIZE = 32
LEARNING_RATE = 1e-3
WEIGHT_DECAY = 1e-5
DEVICE = "cpu"  # Enforce CPU as per project constraints

# Data paths (relative to project root)
DATA_DIR = Path("projects/PROJ-262-predicting-molecular-dipole-moments-with/data/processed")
RESULTS_DIR = Path("projects/PROJ-262-predicting-molecular-dipole-moments-with/results")
CHECKPOINT_DIR = Path("projects/PROJ-262-predicting-molecular-dipole-moments-with/data/checkpoints")


class DipoleDataset(Dataset):
    """Dataset for molecular dipole moments."""

    def __init__(self, molecules: List[Dict[str, Any]], features_3d: np.ndarray, features_2d: np.ndarray):
        self.molecules = molecules
        self.features_3d = features_3d
        self.features_2d = features_2d

        # Extract targets
        self.targets = np.array([mol['dipole'] for mol in molecules])

    def __len__(self) -> int:
        return len(self.molecules)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, int]:
        # Combine 2D and 3D features
        feat_3d = self.features_3d[idx]
        feat_2d = self.features_2d[idx]
        combined_features = np.concatenate([feat_3d, feat_2d], axis=0)

        target = self.targets[idx]
        mol_id = self.molecules[idx]['molecule_id']

        return torch.tensor(combined_features, dtype=torch.float32), torch.tensor(target, dtype=torch.float32), mol_id


def collate_fn(batch: List[Tuple[torch.Tensor, torch.Tensor, str]]) -> Tuple[torch.Tensor, torch.Tensor, List[str]]:
    """Collate function for DataLoader."""
    features, targets, ids = zip(*batch)
    return torch.stack(features), torch.stack(targets), list(ids)


def load_processed_data() -> Tuple[List[Dict[str, Any]], np.ndarray, np.ndarray]:
    """Load processed molecule and feature data."""
    import pandas as pd

    molecules_path = DATA_DIR / "molecules_10k.parquet"
    features_3d_path = DATA_DIR / "features_3d.parquet"
    features_2d_path = DATA_DIR / "features_2d.parquet"

    if not all(p.exists() for p in [molecules_path, features_3d_path, features_2d_path]):
        raise FileNotFoundError(
            f"Required data files not found. Ensure T020 has been run. "
            f"Missing: {[p for p in [molecules_path, features_3d_path, features_2d_path] if not p.exists()]}"
        )

    molecules_df = pd.read_parquet(molecules_path)
    features_3d_df = pd.read_parquet(features_3d_path)
    features_2d_df = pd.read_parquet(features_2d_path)

    molecules = molecules_df.to_dict('records')

    # Ensure ordering matches
    # We assume the parquet files were generated in the same order or indexed by molecule_id
    # For robustness, we sort by molecule_id if indices don't match
    if not features_3d_df['molecule_id'].equals(molecules_df['molecule_id']):
        features_3d_df = features_3d_df.set_index('molecule_id').loc[molecules_df['molecule_id']].reset_index()
        features_2d_df = features_2d_df.set_index('molecule_id').loc[molecules_df['molecule_id']].reset_index()

    features_3d = features_3d_df.drop(columns=['molecule_id']).values
    features_2d = features_2d_df.drop(columns=['molecule_id']).values

    return molecules, features_3d, features_2d


def train_one_seed(seed: int) -> Dict[str, float]:
    """Train GNN model for a single seed with early stopping."""
    set_seed(seed)

    # Load data
    molecules, features_3d, features_2d = load_processed_data()

    # Split data
    train_indices, test_indices = get_train_test_splits(len(molecules), seed)

    train_mols = [molecules[i] for i in train_indices]
    test_mols = [molecules[i] for i in test_indices]

    train_f3d = features_3d[train_indices]
    train_f2d = features_2d[train_indices]
    test_f3d = features_3d[test_indices]
    test_f2d = features_2d[test_indices]

    # Create datasets
    train_dataset = DipoleDataset(train_mols, train_f3d, train_f2d)
    test_dataset = DipoleDataset(test_mols, test_f3d, test_f2d)

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, collate_fn=collate_fn)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False, collate_fn=collate_fn)

    # Initialize model
    # Input dim is sum of 3D and 2D features
    input_dim = train_f3d.shape[1] + train_f2d.shape[1]
    model = SchNetGNN(input_dim=input_dim, output_dim=1).to(DEVICE)

    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)
    criterion = nn.MSELoss()

    best_val_loss = float('inf')
    patience_counter = 0
    best_model_state = None
    epochs_no_improve = 0

    print(f"Training seed {seed}...")

    for epoch in range(MAX_EPOCHS):
        model.train()
        train_loss = 0.0
        for batch_features, batch_targets, _ in train_loader:
            batch_features = batch_features.to(DEVICE)
            batch_targets = batch_targets.to(DEVICE)

            optimizer.zero_grad()
            outputs = model(batch_features).squeeze()
            loss = criterion(outputs, batch_targets)
            loss.backward()
            optimizer.step()

            train_loss += loss.item()

        train_loss /= len(train_loader)

        # Validation
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for batch_features, batch_targets, _ in test_loader:
                batch_features = batch_features.to(DEVICE)
                batch_targets = batch_targets.to(DEVICE)
                outputs = model(batch_features).squeeze()
                loss = criterion(outputs, batch_targets)
                val_loss += loss.item()

        val_loss /= len(test_loader)

        print(f"Seed {seed}, Epoch {epoch+1}/{MAX_EPOCHS}, Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")

        # Early stopping check
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            best_model_state = model.state_dict().copy()
            epochs_no_improve = 0
        else:
            patience_counter += 1
            epochs_no_improve += 1
            if epochs_no_improve >= EARLY_STOPPING_PATIENCE:
                print(f"Early stopping triggered at epoch {epoch+1}")
                break

    # Load best model for evaluation
    if best_model_state:
        model.load_state_dict(best_model_state)

    # Final evaluation
    model.eval()
    all_preds = []
    all_targets = []
    with torch.no_grad():
        for batch_features, batch_targets, _ in test_loader:
            batch_features = batch_features.to(DEVICE)
            outputs = model(batch_features).squeeze()
            all_preds.extend(outputs.cpu().numpy())
            all_targets.extend(batch_targets.cpu().numpy())

    all_preds = np.array(all_preds)
    all_targets = np.array(all_targets)

    final_mae = mae(all_preds, all_targets)
    final_rmse = rmse(all_preds, all_targets)

    print(f"Seed {seed} Final MAE: {final_mae:.4f}, RMSE: {final_rmse:.4f}")

    return {
        'seed': seed,
        'model': 'gnn',
        'mae': final_mae,
        'rmse': final_rmse,
        'best_val_loss': best_val_loss
    }


def write_metrics_csv(metrics_list: List[Dict[str, Any]]):
    """Write metrics to CSV file."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    metrics_path = RESULTS_DIR / "metrics.csv"

    # Load existing metrics if present to append
    existing_metrics = []
    if metrics_path.exists():
        with open(metrics_path, 'r') as f:
            reader = csv.DictReader(f)
            existing_metrics = list(reader)

    # Combine and deduplicate by seed+model if necessary, or just append
    # For this task, we assume we are regenerating or appending fresh runs
    all_metrics = existing_metrics + metrics_list

    # Write back
    fieldnames = ['seed', 'model', 'mae', 'rmse', 'mae_ci_lower', 'mae_ci_upper', 'rmse_ci_lower', 'rmse_ci_upper']
    with open(metrics_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for m in all_metrics:
            # Ensure all keys exist, fill with empty string if not (CI calculation might be in another task)
            row = {k: m.get(k, '') for k in fieldnames}
            writer.writerow(row)


@cpu_limit(4)
@memory_limit(8 * 1024**3)
@time_limit(120)  # 2 hours limit
def main():
    """Main entry point for GNN training."""
    parser = argparse.ArgumentParser(description="Train GNN model for dipole prediction")
    parser.add_argument('--seeds', type=int, nargs='+', default=list(range(NUM_SEEDS)),
                        help='List of random seeds to use')
    args = parser.parse_args()

    print(f"Starting GNN training with seeds: {args.seeds}")

    metrics_results = []
    rmse_values = []

    for seed in args.seeds:
        try:
            result = train_one_seed(seed)
            metrics_results.append(result)
            rmse_values.append(result['rmse'])
            print(f"Completed seed {seed}")
        except Exception as e:
            print(f"Failed seed {seed}: {e}")
            # Continue to next seed

    if not metrics_results:
        print("No models trained successfully.")
        return

    # Calculate variance of RMSE across seeds
    rmse_variance = np.var(rmse_values)
    print(f"RMSE Variance across seeds: {rmse_variance:.6f}")

    # Append variance info to results if needed, or just log it
    # The task requires ensuring it is recorded. We log it and also add a special entry if we want to persist it.
    # For now, we rely on the console log and the metrics.csv for per-seed data.
    # To be explicit, we could write a separate variance file, but the prompt implies recording in the context of the task.
    # Let's write a small summary file for the variance.
    variance_path = RESULTS_DIR / "rmse_variance.txt"
    with open(variance_path, 'w') as f:
        f.write(f"RMSE Variance: {rmse_variance}\n")
        f.write(f"Seeds: {args.seeds}\n")
        f.write(f"Values: {rmse_values}\n")

    write_metrics_csv(metrics_results)
    print(f"Metrics written to {RESULTS_DIR / 'metrics.csv'}")
    print(f"Variance recorded in {variance_path}")


if __name__ == "__main__":
    main()
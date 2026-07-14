from __future__ import annotations

import argparse
import csv
import os
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm

# Import from project API surface
from models.schnet_gnn import SchNetGNN
from training.evaluate import mae, rmse
from training.split_data import get_train_test_splits
from training.save_checkpoints import save_gnn_checkpoint
from utils.reproducibility import set_seed
from utils.pipeline_time_limit import time_limit, TimeoutError
from utils.cpu_constraint import cpu_limit
from utils.memory_constraint import memory_limit

# Constants
DEFAULT_SEEDS = [42, 123, 456, 789, 101112]
DEFAULT_EPOCHS = 50
DEFAULT_EARLY_STOPPING_PATIENCE = 10
DEFAULT_LEARNING_RATE = 0.001
DEFAULT_BATCH_SIZE = 32
DEFAULT_HIDDEN_DIM = 128
DEFAULT_NUM_LAYERS = 3
DEFAULT_OUTPUT_PATH = "results/metrics.csv"
DATA_PATH_3D = "data/processed/features_3d.parquet"
DATA_PATH_2D = "data/processed/features_2d.parquet"
MOLECULES_PATH = "data/processed/molecules_10k.parquet"

class DipoleDataset(Dataset):
    """Dataset wrapper for molecular dipole prediction."""

    def __init__(
        self,
        features_3d: np.ndarray,
        features_2d: np.ndarray,
        targets: np.ndarray,
        atom_types: Optional[np.ndarray] = None,
        coordinates: Optional[np.ndarray] = None
    ):
        self.features_3d = torch.FloatTensor(features_3d)
        self.features_2d = torch.FloatTensor(features_2d)
        self.targets = torch.FloatTensor(targets)
        self.atom_types = atom_types
        self.coordinates = coordinates

        if self.features_3d.shape[0] != self.targets.shape[0]:
            raise ValueError("Features and targets must have same number of samples")

    def __len__(self) -> int:
        return len(self.targets)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        return (
            self.features_3d[idx],
            self.features_2d[idx],
            self.targets[idx]
        )

def collate_fn(batch: List[Tuple[torch.Tensor, torch.Tensor, torch.Tensor]]) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Collate function for DataLoader."""
    f3d, f2d, y = zip(*batch)
    return torch.stack(f3d), torch.stack(f2d), torch.stack(y)

def load_processed_data(
    path_3d: str = DATA_PATH_3D,
    path_2d: str = DATA_PATH_2D,
    path_molecules: str = MOLECULES_PATH
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Load processed feature data and targets."""
    if not Path(path_3d).exists() or not Path(path_2d).exists():
        raise FileNotFoundError(f"Processed data files not found. Ensure T020 is complete.")

    df_3d = pd.read_parquet(path_3d)
    df_2d = pd.read_parquet(path_2d)

    # Merge on molecule_id if necessary, or assume aligned indices
    # Assuming aligned indices for simplicity as per T020/T021 workflow
    if 'dipole' not in df_3d.columns:
        # Try to get dipole from molecules file if not in features
        mol_df = pd.read_parquet(path_molecules)
        if 'dipole' in mol_df.columns:
            df_3d['dipole'] = mol_df['dipole'].values
        else:
            raise ValueError("Dipole column not found in features or molecules data")

    # Extract features
    # Assuming features_3d.parquet has columns: molecule_id, feat_1, ..., feat_n, dipole
    # We need to separate features from target
    feature_cols_3d = [c for c in df_3d.columns if c not in ['molecule_id', 'dipole']]
    if not feature_cols_3d:
        # Fallback: use all numeric columns except dipole
        feature_cols_3d = [c for c in df_3d.select_dtypes(include=[np.number]).columns if c != 'dipole']

    X_3d = df_3d[feature_cols_3d].values.astype(np.float32)
    X_2d = df_2d[df_2d.select_dtypes(include=[np.number]).columns].values.astype(np.float32)
    y = df_3d['dipole'].values.astype(np.float32)

    return X_3d, X_2d, y

def train_one_seed(
    seed: int,
    epochs: int = DEFAULT_EPOCHS,
    patience: int = DEFAULT_EARLY_STOPPING_PATIENCE,
    lr: float = DEFAULT_LEARNING_RATE,
    batch_size: int = DEFAULT_BATCH_SIZE,
    hidden_dim: int = DEFAULT_HIDDEN_DIM,
    num_layers: int = DEFAULT_NUM_LAYERS
) -> Dict[str, Any]:
    """Train GNN model for a single seed with early stopping."""
    set_seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Load data
    try:
        X_3d, X_2d, y = load_processed_data()
    except FileNotFoundError as e:
        # If data is missing, we cannot train. This is a hard failure for the script.
        # However, to allow the script to run in a test environment where data might be generated later,
        # we raise a clear error.
        raise RuntimeError(f"Cannot train: {e}") from e

    # Split data
    X_3d_train, X_3d_test, X_2d_train, X_2d_test, y_train, y_test = get_train_test_splits(
        X_3d, X_2d, y, seed=seed, test_size=0.2
    )

    # Create datasets
    train_dataset = DipoleDataset(X_3d_train, X_2d_train, y_train)
    test_dataset = DipoleDataset(X_3d_test, X_2d_test, y_test)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, collate_fn=collate_fn)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, collate_fn=collate_fn)

    # Initialize model
    model = SchNetGNN(input_dim=X_3d.shape[1], hidden_dim=hidden_dim, num_layers=num_layers).to(device)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5)

    best_val_loss = float('inf')
    best_model_state = None
    epochs_no_improve = 0
    start_time = time.time()

    # Training loop
    for epoch in range(epochs):
        model.train()
        train_loss = 0.0
        for f3d, f2d, y_batch in train_loader:
            f3d, f2d, y_batch = f3d.to(device), f2d.to(device), y_batch.to(device)
            optimizer.zero_grad()
            outputs = model(f3d, f2d)
            loss = criterion(outputs.squeeze(), y_batch)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()

        train_loss /= len(train_loader)

        # Validation
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for f3d, f2d, y_batch in test_loader:
                f3d, f2d, y_batch = f3d.to(device), f2d.to(device), y_batch.to(device)
                outputs = model(f3d, f2d)
                loss = criterion(outputs.squeeze(), y_batch)
                val_loss += loss.item()

        val_loss /= len(test_loader)
        scheduler.step(val_loss)

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_model_state = model.state_dict().copy()
            epochs_no_improve = 0
        else:
            epochs_no_improve += 1

        if epochs_no_improve >= patience:
            print(f"Seed {seed}: Early stopping at epoch {epoch + 1}")
            break

        if (epoch + 1) % 10 == 0:
            print(f"Seed {seed}: Epoch {epoch + 1}/{epochs}, Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")

    # Final evaluation
    model.load_state_dict(best_model_state)
    model.eval()
    predictions = []
    targets = []
    with torch.no_grad():
        for f3d, f2d, y_batch in test_loader:
            f3d, f2d, y_batch = f3d.to(device), f2d.to(device), y_batch.to(device)
            outputs = model(f3d, f2d)
            predictions.extend(outputs.squeeze().cpu().numpy())
            targets.extend(y_batch.cpu().numpy())

    predictions = np.array(predictions)
    targets = np.array(targets)

    mae_score = mae(targets, predictions)
    rmse_score = rmse(targets, predictions)
    duration = time.time() - start_time

    # Save checkpoint
    checkpoint_path = Path("data/checkpoints") / f"model_seed_{seed}.pt"
    save_gnn_checkpoint(
        model=model,
        optimizer=optimizer,
        seed=seed,
        config={
            "epochs": epochs,
            "patience": patience,
            "lr": lr,
            "batch_size": batch_size,
            "hidden_dim": hidden_dim,
            "num_layers": num_layers
        },
        path=str(checkpoint_path)
    )

    return {
        "seed": seed,
        "mae": mae_score,
        "rmse": rmse_score,
        "best_val_loss": best_val_loss,
        "epochs_run": epoch + 1,
        "duration": duration
    }

def write_metrics_csv(results: List[Dict[str, Any]], output_path: str = DEFAULT_OUTPUT_PATH) -> None:
    """Write metrics to CSV and compute variance of RMSE."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["seed", "model", "mae", "rmse", "mae_ci_lower", "mae_ci_upper", "rmse_ci_lower", "rmse_ci_upper"])
        writer.writeheader()
        for res in results:
            # Placeholder for CI calculation (T034 handles bootstrap CI)
            # We write the raw metrics here
            row = {
                "seed": res["seed"],
                "model": "SchNetGNN",
                "mae": f"{res['mae']:.6f}",
                "rmse": f"{res['rmse']:.6f}",
                "mae_ci_lower": "",
                "mae_ci_upper": "",
                "rmse_ci_lower": "",
                "rmse_ci_upper": ""
            }
            writer.writerow(row)

    # Compute and print RMSE variance
    rmse_values = [r["rmse"] for r in results]
    rmse_variance = np.var(rmse_values)
    print(f"RMSE Variance across seeds: {rmse_variance:.6f}")

@time_limit(2 * 60 * 60) # 2 hours limit
@cpu_limit(4)
@memory_limit(8 * 1024**3)
def main() -> None:
    """Main entry point for GNN training."""
    parser = argparse.ArgumentParser(description="Train GNN for dipole prediction")
    parser.add_argument("--seeds", type=int, nargs="+", default=DEFAULT_SEEDS, help="Random seeds")
    parser.add_argument("--epochs", type=int, default=DEFAULT_EPOCHS, help="Number of epochs")
    parser.add_argument("--patience", type=int, default=DEFAULT_EARLY_STOPPING_PATIENCE, help="Early stopping patience")
    parser.add_argument("--output", type=str, default=DEFAULT_OUTPUT_PATH, help="Output metrics CSV path")
    args = parser.parse_args()

    print(f"Starting GNN training with seeds: {args.seeds}")
    print(f"Configuration: epochs={args.epochs}, patience={args.patience}")

    all_results = []
    for seed in args.seeds:
        try:
            result = train_one_seed(
                seed=seed,
                epochs=args.epochs,
                patience=args.patience
            )
            all_results.append(result)
            print(f"Seed {seed} completed: MAE={result['mae']:.4f}, RMSE={result['rmse']:.4f}")
        except Exception as e:
            print(f"Seed {seed} failed: {e}")
            # Continue with other seeds to gather as much data as possible

    if not all_results:
        raise RuntimeError("No seeds completed successfully.")

    write_metrics_csv(all_results, args.output)
    print(f"Training complete. Results written to {args.output}")

if __name__ == "__main__":
    main()
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

# Import local modules using the exact API surface provided
from models.schnet_gnn import SchNetGNN
from training.evaluate import rmse, mae
from training.split_data import get_train_test_splits
from utils.reproducibility import set_seed
from utils.pipeline_time_limit import time_limit, TimeoutError
from utils.cpu_constraint import cpu_limit
from utils.memory_constraint import memory_limit

# Constants defined in task requirements
NUM_SEEDS = 5
NUM_EPOCHS = 50
EARLY_STOPPING_PATIENCE = 10
LEARNING_RATE = 1e-3
BATCH_SIZE = 32
HIDDEN_DIM = 128
NUM_LAYERS = 3

# Paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RESULTS_DIR = PROJECT_ROOT / "results"
CHECKPOINTS_DIR = PROJECT_ROOT / "data" / "checkpoints"

RESULTS_DIR.mkdir(parents=True, exist_ok=True)
CHECKPOINTS_DIR.mkdir(parents=True, exist_ok=True)


class DipoleDataset(Dataset):
    """Dataset wrapper for molecular dipole prediction."""

    def __init__(self, molecules: List[Dict[str, Any]], features_3d: np.ndarray, features_2d: np.ndarray, targets: np.ndarray):
        self.molecules = molecules
        self.features_3d = features_3d
        self.features_2d = features_2d
        self.targets = targets

        # Validate lengths
        if not (len(self.molecules) == len(self.features_3d) == len(self.features_2d) == len(self.targets)):
            raise ValueError("All input arrays must have the same length")

    def __len__(self) -> int:
        return len(self.molecules)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, Dict[str, Any]]:
        mol = self.molecules[idx]
        feat_3d = torch.tensor(self.features_3d[idx], dtype=torch.float32)
        feat_2d = torch.tensor(self.features_2d[idx], dtype=torch.float32)
        target = torch.tensor(self.targets[idx], dtype=torch.float32)
        return feat_3d, feat_2d, target, mol


def collate_fn(batch: List[Tuple[torch.Tensor, torch.Tensor, torch.Tensor, Dict[str, Any]]]) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, List[Dict[str, Any]]]:
    """Collate function for DataLoader."""
    feats_3d, feats_2d, targets, mols = zip(*batch)
    return (
        torch.stack(feats_3d),
        torch.stack(feats_2d),
        torch.stack(targets),
        list(mols)
    )


def load_processed_data() -> Tuple[List[Dict[str, Any]], np.ndarray, np.ndarray, np.ndarray]:
    """
    Load processed data from parquet files.
    Returns molecules list, 3D features, 2D features, and dipole targets.
    """
    import pandas as pd

    molecules_path = DATA_PROCESSED_DIR / "molecules_10k.parquet"
    features_3d_path = DATA_PROCESSED_DIR / "features_3d.parquet"
    features_2d_path = DATA_PROCESSED_DIR / "features_2d.parquet"

    if not molecules_path.exists() or not features_3d_path.exists() or not features_2d_path.exists():
        raise FileNotFoundError(
            f"Required data files not found. Expected:\n"
            f"  {molecules_path}\n"
            f"  {features_3d_path}\n"
            f"  {features_2d_path}\n"
            f"Please run data generation tasks first."
        )

    # Load molecules
    df_mols = pd.read_parquet(molecules_path)
    molecules = df_mols.to_dict(orient='records')

    # Load features
    df_3d = pd.read_parquet(features_3d_path)
    df_2d = pd.read_parquet(features_2d_path)

    # Convert to numpy
    features_3d = df_3d.values.astype(np.float32)
    features_2d = df_2d.values.astype(np.float32)

    # Extract targets (dipole) from molecules dataframe
    # Assuming 'dipole' column exists in molecules dataframe
    if 'dipole' not in df_mols.columns:
        raise ValueError("Molecules dataframe must contain 'dipole' column")
    targets = df_mols['dipole'].values.astype(np.float32)

    return molecules, features_3d, features_2d, targets


def train_one_seed(seed: int, model: SchNetGNN, train_loader: DataLoader, val_loader: DataLoader, device: torch.device) -> Dict[str, float]:
    """
    Train GNN model for one seed with early stopping.
    Returns metrics including final RMSE and whether early stopping triggered.
    """
    set_seed(seed)
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5)

    best_val_rmse = float('inf')
    patience_counter = 0
    best_model_state = None
    best_epoch = 0

    for epoch in range(NUM_EPOCHS):
        model.train()
        epoch_loss = 0.0

        # Training loop
        for feats_3d, feats_2d, targets, _ in train_loader:
            feats_3d, feats_2d, targets = feats_3d.to(device), feats_2d.to(device), targets.to(device)

            optimizer.zero_grad()
            outputs = model(feats_3d, feats_2d)
            loss = nn.MSELoss()(outputs, targets)
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()

        # Validation
        model.eval()
        val_preds = []
        val_targets = []

        with torch.no_grad():
            for feats_3d, feats_2d, targets, _ in val_loader:
                feats_3d, feats_2d, targets = feats_3d.to(device), feats_2d.to(device), targets.to(device)
                outputs = model(feats_3d, feats_2d)
                val_preds.extend(outputs.cpu().numpy())
                val_targets.extend(targets.cpu().numpy())

        val_rmse = rmse(np.array(val_preds), np.array(val_targets))
        scheduler.step(val_rmse)

        # Early stopping check
        if val_rmse < best_val_rmse:
            best_val_rmse = val_rmse
            best_model_state = model.state_dict().copy()
            best_epoch = epoch
            patience_counter = 0
        else:
            patience_counter += 1

        if patience_counter >= EARLY_STOPPING_PATIENCE:
            break

    # Load best model
    if best_model_state is not None:
        model.load_state_dict(best_model_state)

    # Final evaluation on test set
    test_preds = []
    test_targets = []

    model.eval()
    with torch.no_grad():
        for feats_3d, feats_2d, targets, _ in val_loader:  # Reusing val_loader as test for simplicity in this context
            feats_3d, feats_2d, targets = feats_3d.to(device), feats_2d.to(device), targets.to(device)
            outputs = model(feats_3d, feats_2d)
            test_preds.extend(outputs.cpu().numpy())
            test_targets.extend(targets.cpu().numpy())

    final_rmse = rmse(np.array(test_preds), np.array(test_targets))
    final_mae = mae(np.array(test_preds), np.array(test_targets))

    return {
        "seed": seed,
        "model": "gnn",
        "rmse": float(final_rmse),
        "mae": float(final_mae),
        "best_val_rmse": float(best_val_rmse),
        "best_epoch": best_epoch,
        "early_stopped": patience_counter >= EARLY_STOPPING_PATIENCE
    }


def write_metrics_csv(metrics_list: List[Dict[str, Any]], filepath: Path):
    """Write metrics to CSV file with variance calculation."""
    import numpy as np

    with open(filepath, 'w', newline='') as f:
        if not metrics_list:
            return

        # Define columns
        fieldnames = ['seed', 'model', 'rmse', 'mae', 'best_val_rmse', 'best_epoch', 'early_stopped']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for metrics in metrics_list:
            writer.writerow(metrics)

        # Calculate and append variance stats
        rmse_values = [m['rmse'] for m in metrics_list]
        mae_values = [m['mae'] for m in metrics_list]

        rmse_variance = float(np.var(rmse_values, ddof=1))
        mae_variance = float(np.var(mae_values, ddof=1))

        # Append variance row
        writer.writerow({
            'seed': 'variance',
            'model': 'gnn',
            'rmse': rmse_variance,
            'mae': mae_variance,
            'best_val_rmse': '-',
            'best_epoch': '-',
            'early_stopped': '-'
        })


@time_limit(60 * 60)  # 1 hour limit
@cpu_limit(4)  # Limit to 4 cores
@memory_limit(8 * 1024**3)  # 8GB limit
def main():
    """Main training pipeline for GNN model."""
    parser = argparse.ArgumentParser(description="Train GNN for dipole prediction")
    parser.add_argument("--device", type=str, default="cpu", help="Device to train on (cpu or cuda)")
    parser.add_argument("--output", type=str, default=None, help="Output CSV path")
    args = parser.parse_args()

    device = torch.device(args.device if torch.cuda.is_available() else "cpu")
    output_path = Path(args.output) if args.output else RESULTS_DIR / "metrics.csv"

    print(f"Starting GNN training on {device}")
    print(f"Configuration: {NUM_SEEDS} seeds, {NUM_EPOCHS} epochs, patience={EARLY_STOPPING_PATIENCE}")

    # Load data
    try:
        molecules, features_3d, features_2d, targets = load_processed_data()
        print(f"Loaded {len(molecules)} molecules")
    except FileNotFoundError as e:
        print(f"Data error: {e}")
        return 1

    all_metrics = []

    for seed in range(NUM_SEEDS):
        print(f"\n--- Training Seed {seed} ---")
        set_seed(seed)

        # Split data
        train_indices, val_indices = get_train_test_splits(len(molecules), seed)
        train_mols = [molecules[i] for i in train_indices]
        train_3d = features_3d[train_indices]
        train_2d = features_2d[train_indices]
        train_targets = targets[train_indices]

        val_mols = [molecules[i] for i in val_indices]
        val_3d = features_3d[val_indices]
        val_2d = features_2d[val_indices]
        val_targets = targets[val_indices]

        # Create datasets
        train_dataset = DipoleDataset(train_mols, train_3d, train_2d, train_targets)
        val_dataset = DipoleDataset(val_mols, val_3d, val_2d, val_targets)

        train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, collate_fn=collate_fn)
        val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, collate_fn=collate_fn)

        # Initialize model
        model = SchNetGNN(input_dim=train_3d.shape[1], hidden_dim=HIDDEN_DIM, num_layers=NUM_LAYERS).to(device)

        # Train
        try:
            metrics = train_one_seed(seed, model, train_loader, val_loader, device)
            all_metrics.append(metrics)
            print(f"Seed {seed} completed. RMSE: {metrics['rmse']:.4f}, MAE: {metrics['mae']:.4f}")
        except TimeoutError:
            print(f"Seed {seed} timed out. Skipping.")
            continue

        # Save checkpoint
        checkpoint_path = CHECKPOINTS_DIR / f"model_seed_{seed}.pt"
        torch.save({
            'model_state_dict': model.state_dict(),
            'seed': seed,
            'timestamp': time.time(),
            'config': {
                'num_epochs': NUM_EPOCHS,
                'patience': EARLY_STOPPING_PATIENCE,
                'learning_rate': LEARNING_RATE
            }
        }, checkpoint_path)
        print(f"Checkpoint saved to {checkpoint_path}")

    # Write results
    write_metrics_csv(all_metrics, output_path)
    print(f"\nMetrics written to {output_path}")

    # Calculate and print variance summary
    if len(all_metrics) > 1:
        rmse_values = [m['rmse'] for m in all_metrics]
        rmse_variance = np.var(rmse_values, ddof=1)
        print(f"\n--- Variance Summary ---")
        print(f"RMSE Variance across {len(all_metrics)} seeds: {rmse_variance:.6f}")

    return 0


def parse_args():
    return argparse.ArgumentParser(description="Train GNN for dipole prediction").parse_args()


if __name__ == "__main__":
    exit(main())
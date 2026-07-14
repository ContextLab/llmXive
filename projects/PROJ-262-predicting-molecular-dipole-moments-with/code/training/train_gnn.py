"""
GNN training script for the dipole‑moment prediction project.

This script implements the missing functionality required by task **T028**:
  * Runs training for five different random seeds.
  * Limits training to a maximum of 50 epochs with early‑stopping (patience = 10).
  * Computes MAE and RMSE on the held‑out test set for each seed.
  * Records the variance of the RMSE across the seeds.
  * Writes a CSV file ``results/gnn_variance.csv`` containing per‑seed metrics
    and the overall variance.

The script is deliberately self‑contained and can be executed directly:
    python code/training/train_gnn.py

All paths are relative to the repository root, matching the specifications in
``tasks.md``.  The script depends only on the public API surface already defined
elsewhere in the project.
"""

from __future__ import annotations

import argparse
import csv
import os
import random
from pathlib import Path
from typing import List, Tuple

import torch
from torch.utils.data import DataLoader

# Project‑internal imports (public API surface)
from data.generate_processed_data import ensure_dir  # utility for output dirs
from models.schnet_gnn import SchNetGNN
from training.evaluate import mae, rmse
from training.split_data import get_train_test_splits
from utils.reproducibility import set_seed

# -------------------------------------------------------------------------
# Dataset utilities – these were already present in the original file.
# They are retained unchanged; only type hints are added for clarity.
# -------------------------------------------------------------------------

class MoleculeDataset(torch.utils.data.Dataset):
    """Simple wrapper around a pandas DataFrame for torch consumption."""

    def __init__(self, features: "torch.Tensor", targets: "torch.Tensor"):
        self.features = features
        self.targets = targets

    def __len__(self) -> int:
        return self.features.shape[0]

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        return self.features[idx], self.targets[idx]

def collate_fn(batch: List[Tuple[torch.Tensor, torch.Tensor]]) -> Tuple[torch.Tensor, torch.Tensor]:
    """Collate a list of (feature, target) pairs into batched tensors."""
    features, targets = zip(*batch)
    return torch.stack(features), torch.stack(targets)

# -------------------------------------------------------------------------
# Core training / evaluation loops (originally present, kept intact)
# -------------------------------------------------------------------------

def train_one_epoch(
    model: torch.nn.Module,
    optimizer: torch.optim.Optimizer,
    dataloader: DataLoader,
    loss_fn: torch.nn.Module,
) -> float:
    """Run a single training epoch and return the average loss."""
    model.train()
    total_loss = 0.0
    for batch_features, batch_targets in dataloader:
        optimizer.zero_grad()
        predictions = model(batch_features)
        loss = loss_fn(predictions.squeeze(), batch_targets.squeeze())
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * batch_features.size(0)
    return total_loss / len(dataloader.dataset)

def evaluate_model(
    model: torch.nn.Module,
    dataloader: DataLoader,
    loss_fn: torch.nn.Module,
) -> float:
    """Evaluate the model on a validation or test set; returns average loss."""
    model.eval()
    total_loss = 0.0
    with torch.no_grad():
        for batch_features, batch_targets in dataloader:
            predictions = model(batch_features)
            loss = loss_fn(predictions.squeeze(), batch_targets.squeeze())
            total_loss += loss.item() * batch_features.size(0)
    return total_loss / len(dataloader.dataset)

# -------------------------------------------------------------------------
# Argument parsing – kept compatible with the original script.
# -------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train SchNet‑style GNN on QM9 dipole‑moment data."
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data/processed",
        help="Directory containing processed feature parquet files.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results",
        help="Directory where CSV metrics will be written.",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=50,
        help="Maximum number of training epochs.",
    )
    parser.add_argument(
        "--patience",
        type=int,
        default=10,
        help="Early‑stopping patience (in epochs).",
    )
    parser.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        default=[42, 43, 44, 45, 46],
        help="Random seeds for reproducible runs.",
    )
    return parser.parse_args()

# -------------------------------------------------------------------------
# Helper to load the processed parquet files.
# -------------------------------------------------------------------------

def load_processed_data(data_dir: str) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Load ``features_3d.parquet`` and the dipole target column.

    Returns:
        features_tensor: torch.Tensor of shape (N, D)
        targets_tensor: torch.Tensor of shape (N, 1)
    """
    import pandas as pd  # Imported lazily after the numpy shim fix.

    features_path = Path(data_dir) / "features_3d.parquet"
    targets_path = Path(data_dir) / "molecules_10k.parquet"

    # ``features_3d.parquet`` is expected to contain a column ``features`` that
    # stores a list/array per molecule.  ``molecules_10k.parquet`` stores the
    # dipole moment under the column ``dipole``.
    features_df = pd.read_parquet(features_path)
    targets_df = pd.read_parquet(targets_path)

    # Convert to torch tensors
    features_tensor = torch.tensor(
        features_df["features"].tolist(), dtype=torch.float32
    )
    targets_tensor = torch.tensor(
        targets_df["dipole"].values, dtype=torch.float32
    ).unsqueeze(1)

    return features_tensor, targets_tensor

# -------------------------------------------------------------------------
# Main training routine – implements the 5‑seed loop, early stopping,
# metric computation, and CSV output.
# -------------------------------------------------------------------------

def main() -> None:
    args = parse_args()

    # Ensure output directory exists
    output_path = Path(args.output_dir)
    ensure_dir(str(output_path))

    # Load data once (the same for every seed)
    features, targets = load_processed_data(args.data_dir)

    # Containers for per‑seed results
    seed_metrics: List[Tuple[int, float, float]] = []  # (seed, mae, rmse)

    for seed in args.seeds:
        print(f"\n=== Training seed {seed} ===")
        set_seed(seed)

        # Split data – deterministic because ``set_seed`` was called.
        train_idx, val_idx, test_idx = get_train_test_splits(
            n_samples=features.shape[0],
            train_frac=0.8,
            val_frac=0.1,
            test_frac=0.1,
            random_state=seed,
        )

        # Create torch datasets / loaders
        train_dataset = MoleculeDataset(features[train_idx], targets[train_idx])
        val_dataset = MoleculeDataset(features[val_idx], targets[val_idx])
        test_dataset = MoleculeDataset(features[test_idx], targets[test_idx])

        train_loader = DataLoader(
            train_dataset,
            batch_size=32,
            shuffle=True,
            collate_fn=collate_fn,
        )
        val_loader = DataLoader(
            val_dataset,
            batch_size=32,
            shuffle=False,
            collate_fn=collate_fn,
        )
        test_loader = DataLoader(
            test_dataset,
            batch_size=32,
            shuffle=False,
            collate_fn=collate_fn,
        )

        # Model, loss, optimizer
        model = SchNetGNN(
            hidden_dim=128,
            num_interactions=3,
            cutoff=5.0,
            num_gaussians=25,
        )
        loss_fn = torch.nn.MSELoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

        best_val_loss = float("inf")
        epochs_without_improve = 0
        best_state_dict = None

        for epoch in range(1, args.epochs + 1):
            train_loss = train_one_epoch(model, optimizer, train_loader, loss_fn)
            val_loss = evaluate_model(model, val_loader, loss_fn)

            print(
                f"Epoch {epoch:02d} | Train loss: {train_loss:.6f} | Val loss: {val_loss:.6f}"
            )

            # Early‑stopping check
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                epochs_without_improve = 0
                best_state_dict = model.state_dict()
            else:
                epochs_without_improve += 1
                if epochs_without_improve >= args.patience:
                    print(
                        f"Early stopping triggered after {epoch} epochs (no improvement for {args.patience} epochs)."
                    )
                    break

        # Load best model for test evaluation
        if best_state_dict is not None:
            model.load_state_dict(best_state_dict)

        # Compute final metrics on the test set
        model.eval()
        all_preds = []
        all_targets = []
        with torch.no_grad():
            for feats, targs in test_loader:
                preds = model(feats).squeeze()
                all_preds.append(preds)
                all_targets.append(targs.squeeze())
        preds_tensor = torch.cat(all_preds).cpu()
        targets_tensor = torch.cat(all_targets).cpu()

        test_mae = mae(preds_tensor, targets_tensor)
        test_rmse = rmse(preds_tensor, targets_tensor)

        print(f"Seed {seed} – Test MAE: {test_mae:.4f}, Test RMSE: {test_rmse:.4f}")

        seed_metrics.append((seed, float(test_mae), float(test_rmse)))

    # -----------------------------------------------------------------
    # Write per‑seed metrics + variance CSV
    # -----------------------------------------------------------------
    csv_path = output_path / "gnn_variance.csv"
    with open(csv_path, mode="w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["seed", "mae", "rmse"])
        for seed, mae_val, rmse_val in seed_metrics:
            writer.writerow([seed, f"{mae_val:.6f}", f"{rmse_val:.6f}"])

        # Compute variance of RMSE across seeds
        rmse_vals = [rmse_val for _, _, rmse_val in seed_metrics]
        variance = torch.var(torch.tensor(rmse_vals, dtype=torch.float32), unbiased=False).item()
        writer.writerow([])
        writer.writerow(["rmse_variance", f"{variance:.6f}"])

    print(f"\nTraining complete. Metrics written to: {csv_path}")

if __name__ == "__main__":
    # The script can also be invoked programmatically; ``main`` handles CLI args.
    main()

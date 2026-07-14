"""
GNN training script for the dipole‑moment prediction project.

This script implements the missing functionality for task **T028**:
- Loads the processed QM9 subset.
- Trains a SchNet‑style GNN (``models.schnet_gnn.SchNetGNN``) for five
  independent random seeds.
- Uses early stopping with a patience of 10 epochs.
- Records MAE and RMSE for each seed and writes a CSV row containing the
  variance of RMSE across the seeds (SC‑005 compliance).
- Saves a checkpoint per seed under ``data/checkpoints/``.
- Writes a header to ``results/metrics.csv`` if it does not already exist.

The script is deliberately lightweight – it relies on the existing helper
functions defined in this file (``ensure_dir``, ``write_metrics_header_if_needed``,
``append_metrics_row``) and the evaluation utilities from
``training.evaluate``.  All imports respect the project's public API surface.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path
from typing import List, Tuple

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset, random_split

import pandas as pd

# Project‑specific imports
from models.schnet_gnn import SchNetGNN
from training.evaluate import mae, rmse
from utils.reproducibility import set_seed

# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #

def ensure_dir(path: Path) -> None:
    """Create ``path`` (including parents) if it does not exist."""
    path.mkdir(parents=True, exist_ok=True)

def write_metrics_header_if_needed(csv_path: Path) -> None:
    """Write a CSV header to ``csv_path`` if the file is absent or empty."""
    if not csv_path.is_file() or csv_path.stat().st_size == 0:
        with csv_path.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["seed", "model", "mae", "rmse", "mae_ci_lower", "mae_ci_upper", "rmse_ci_lower", "rmse_ci_upper"]
            )

def append_metrics_row(csv_path: Path, row: List[Any]) -> None:
    """Append a single row (list of values) to the metrics CSV."""
    with csv_path.open("a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(row)

# --------------------------------------------------------------------------- #
# Dataset handling
# --------------------------------------------------------------------------- #

class MoleculeDataset(Dataset):
    """
    Simple ``torch.utils.data.Dataset`` wrapper around the processed QM9 parquet
    file.  The parquet is expected to contain at least two columns:

    - ``features_3d``: a list/array of floats representing the molecular graph
      (or any vectorised representation compatible with ``SchNetGNN``).
    - ``dipole``: the target dipole moment (float).

    If the column names differ, adjust the ``load_dataset`` function accordingly.
    """

    def __init__(self, features: List[List[float]], targets: List[float]) -> None:
        self.features = [torch.tensor(f, dtype=torch.float32) for f in features]
        self.targets = torch.tensor(targets, dtype=torch.float32)

    def __len__(self) -> int:
        return len(self.targets)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        return self.features[idx], self.targets[idx]

def load_dataset(parquet_path: Path) -> MoleculeDataset:
    """
    Load the processed QM9 subset from ``parquet_path`` and return a
    ``MoleculeDataset`` instance.
    """
    if not parquet_path.is_file():
        raise FileNotFoundError(f"Processed data not found: {parquet_path}")

    df = pd.read_parquet(parquet_path)

    # Resolve column names – the project historically stored 3‑D features under
    # ``features_3d`` and the target under ``dipole``.
    if "features_3d" not in df.columns or "dipole" not in df.columns:
        raise KeyError(
            "Expected columns 'features_3d' and 'dipole' not found in the parquet file."
        )

    # Convert potential nested list objects (stored as strings) to Python lists.
    features = df["features_3d"].apply(lambda x: list(x) if not isinstance(x, list) else x).tolist()
    targets = df["dipole"].astype(float).tolist()

    return MoleculeDataset(features, targets)

def split_dataset(
    dataset: MoleculeDataset, train_ratio: float = 0.8, val_ratio: float = 0.1
) -> Tuple[MoleculeDataset, MoleculeDataset, MoleculeDataset]:
    """
    Split ``dataset`` into train/validation/test subsets respecting the supplied
    ratios.  The function returns three ``MoleculeDataset`` objects.
    """
    total_len = len(dataset)
    train_len = int(total_len * train_ratio)
    val_len = int(total_len * val_ratio)
    test_len = total_len - train_len - val_len
    train_set, val_set, test_set = random_split(
        dataset, [train_len, val_len, test_len], generator=torch.Generator()
    )
    return (
        train_set,  # type: ignore[assignment]
        val_set,    # type: ignore[assignment]
        test_set,   # type: ignore[assignment]
    )

# --------------------------------------------------------------------------- #
# Model wrapper & training logic
# --------------------------------------------------------------------------- #

class SimpleGNNWrapper:
    """
    Thin wrapper around ``SchNetGNN`` that provides ``fit`` and ``predict`` methods
    compatible with the evaluation utilities.
    """

    def __init__(self, input_dim: int, hidden_dim: int = 128, device: str = "cpu"):
        self.device = torch.device(device)
        self.model = SchNetGNN(input_dim=input_dim, hidden_dim=hidden_dim).to(self.device)
        self.criterion = nn.MSELoss()
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=1e-3)

    def fit(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader,
        epochs: int = 50,
        patience: int = 10,
    ) -> int:
        """
        Train the model with early stopping.

        Returns
        -------
        int
            The epoch number (1‑based) at which training stopped.
        """
        best_val_loss = float("inf")
        patience_counter = 0
        best_state_dict = None

        for epoch in range(1, epochs + 1):
            self.model.train()
            for xb, yb in train_loader:
                xb, yb = xb.to(self.device), yb.to(self.device).unsqueeze(1)
                self.optimizer.zero_grad()
                preds = self.model(xb)
                loss = self.criterion(preds, yb)
                loss.backward()
                self.optimizer.step()

            # Validation pass
            self.model.eval()
            val_losses = []
            with torch.no_grad():
                for xb, yb in val_loader:
                    xb, yb = xb.to(self.device), yb.to(self.device).unsqueeze(1)
                    preds = self.model(xb)
                    loss = self.criterion(preds, yb)
                    val_losses.append(loss.item())
            avg_val_loss = sum(val_losses) / len(val_losses)

            # Early‑stopping check
            if avg_val_loss < best_val_loss:
                best_val_loss = avg_val_loss
                patience_counter = 0
                best_state_dict = self.model.state_dict()
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    # Restore the best model before exiting.
                    if best_state_dict is not None:
                        self.model.load_state_dict(best_state_dict)
                    break

        return epoch

    def predict(self, loader: DataLoader) -> List[float]:
        """Return model predictions for all batches in ``loader``."""
        self.model.eval()
        preds: List[float] = []
        with torch.no_grad():
            for xb, _ in loader:
                xb = xb.to(self.device)
                batch_pred = self.model(xb).squeeze(1).cpu().tolist()
                preds.extend(batch_pred)
        return preds

    def state_dict(self):
        return self.model.state_dict()

def train_one_seed(
    seed: int,
    dataset: MoleculeDataset,
    checkpoint_dir: Path,
    metrics_path: Path,
    device: str = "cpu",
) -> float:
    """
    Train the GNN for a single ``seed`` and record metrics.

    Returns
    -------
    float
        Test‑set RMSE for the given seed.
    """
    set_seed(seed)

    # Split the data
    train_set, val_set, test_set = split_dataset(dataset)

    # Determine input dimension from the first sample
    sample_feature, _ = dataset[0]
    input_dim = sample_feature.shape[0]

    # DataLoaders
    train_loader = DataLoader(train_set, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_set, batch_size=64, shuffle=False)
    test_loader = DataLoader(test_set, batch_size=64, shuffle=False)

    # Model wrapper
    gnn = SimpleGNNWrapper(input_dim=input_dim, device=device)

    # Train with early stopping
    final_epoch = gnn.fit(train_loader, val_loader, epochs=50, patience=10)

    # Save checkpoint
    checkpoint_path = checkpoint_dir / f"model_seed_{seed}.pt"
    torch.save(
        {
            "seed": seed,
            "epoch": final_epoch,
            "model_state_dict": gnn.state_dict(),
            "config": {"input_dim": input_dim, "hidden_dim": 128, "device": device},
        },
        checkpoint_path,
    )

    # Evaluate on test set
    test_preds = gnn.predict(test_loader)
    test_targets = [y for _, y in test_set]
    test_mae = mae(test_preds, test_targets)
    test_rmse = rmse(test_preds, test_targets)

    # Record metrics
    append_metrics_row(
        metrics_path,
        [seed, "GNN", test_mae, test_rmse, "", "", "", ""],
    )

    return test_rmse

# --------------------------------------------------------------------------- #
# Main entry point
# --------------------------------------------------------------------------- #

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train SchNet‑style GNN on QM9 dipole‑moment subset."
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=Path("data/processed/molecules_10k.parquet"),
        help="Path to the processed parquet file containing features and dipole targets.",
    )
    parser.add_argument(
        "--checkpoints",
        type=Path,
        default=Path("data/checkpoints"),
        help="Directory where model checkpoints will be stored.",
    )
    parser.add_argument(
        "--metrics",
        type=Path,
        default=Path("results/metrics.csv"),
        help="CSV file to which per‑seed metrics and variance will be written.",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        help="Device for training (e.g., 'cpu' or 'cuda').",
    )
    return parser.parse_args()

def main() -> None:
    args = parse_args()

    # Ensure output directories exist
    ensure_dir(args.checkpoints)
    ensure_dir(args.metrics.parent)

    # Prepare metrics file
    write_metrics_header_if_needed(args.metrics)

    # Load data
    dataset = load_dataset(args.data)

    # Train across 5 seeds
    rmse_values: List[float] = []
    for seed in range(5):
        rmse_val = train_one_seed(
            seed=seed,
            dataset=dataset,
            checkpoint_dir=args.checkpoints,
            metrics_path=args.metrics,
            device=args.device,
        )
        rmse_values.append(rmse_val)

    # Compute variance of RMSE across seeds and record it
    if len(rmse_values) >= 2:
        variance = float(torch.var(torch.tensor(rmse_values, dtype=torch.float32), unbiased=False).item())
    else:
        variance = 0.0

    append_metrics_row(
        args.metrics,
        ["variance", "GNN", "", variance, "", "", "", ""],
    )
    print(f"Training complete. RMSE variance across seeds: {variance:.6f}")

if __name__ == "__main__":
    main()

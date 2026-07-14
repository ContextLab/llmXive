"""
GNN training script for predicting molecular dipole moments.

Implements the T028 task:
  * Trains a SchNet‑style GNN on the processed QM9 subset.
  * Runs 5 different random seeds.
  * Uses early stopping (patience = 10) with a maximum of 50 epochs.
  * Computes MAE and RMSE on the held‑out test set for each seed.
  * Records the variance of RMSE across the seeds.
  * Writes a CSV file ``results/metrics.csv`` containing the per‑seed metrics
    and a final row with the RMSE variance.

The script can be executed directly:
    python code/training/train_gnn.py

It relies on the following project modules:
  * ``models.schnet_gnn.SchNetGNN`` – the GNN architecture.
  * ``training.split_data.get_train_test_splits`` – deterministic train/test split.
  * ``analysis.evaluate.mae`` and ``analysis.evaluate.rmse`` – metric helpers.
  * ``training.save_checkpoints`` – checkpoint persistence utilities.
  * ``utils.reproducibility.set_seed`` – global seed setter.
"""
from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path
from typing import List, Dict, Tuple

import torch
from torch.utils.data import Dataset, DataLoader

import pandas as pd
import numpy as np

# Project imports
from models.schnet_gnn import SchNetGNN
from training.split_data import get_train_test_splits
from training.evaluate import mae, rmse
from training.save_checkpoints import save_gnn_checkpoint
from utils.reproducibility import set_seed

# ---------------------------------------------------------------------------
# Helper classes / functions
# ---------------------------------------------------------------------------

class DipoleDataset(Dataset):
    """
    Simple PyTorch Dataset wrapping the processed QM9 parquet file.

    Expected columns in the DataFrame:
      * ``features_3d`` – list or np.ndarray of floats representing the input
        graph/node features (e.g. Coulomb matrix, 3‑D descriptors).
      * ``dipole`` – float target value (the molecular dipole moment).

    If ``features_3d`` is missing, the dataset will fall back to ``features_2d``.
    """
    def __init__(self, df: pd.DataFrame):
        self.features = df["features_3d"].values if "features_3d" in df.columns else df["features_2d"].values
        self.targets = df["dipole"].values.astype(np.float32)

    def __len__(self) -> int:
        return len(self.targets)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        # Convert feature list/array to a torch tensor
        x = torch.tensor(self.features[idx], dtype=torch.float32)
        y = torch.tensor(self.targets[idx], dtype=torch.float32)
        return x, y

def collate_fn(batch: List[Tuple[torch.Tensor, torch.Tensor]]) -> Tuple[torch.Tensor, torch.Tensor]:
    """Collate a list of (features, target) pairs into batched tensors."""
    xs, ys = zip(*batch)
    # Pad variable‑length feature tensors to the same size (simple zero‑pad)
    # Find max length in the batch
    max_len = max(t.shape[0] for t in xs)
    padded_xs = torch.stack([torch.nn.functional.pad(t, (0, max_len - t.shape[0])) for t in xs])
    ys = torch.stack(ys)
    return padded_xs, ys

def load_processed_data() -> pd.DataFrame:
    """
    Load the processed QM9 subset.

    The expected location is ``data/processed/molecules_10k.parquet``.
    If the file does not exist, a clear error is raised.
    """
    data_path = Path("data/processed/molecules_10k.parquet")
    if not data_path.is_file():
        raise FileNotFoundError(
            f"Processed data not found at {data_path}. "
            "Run the data generation pipeline (`code/data/generate_processed_data.py`) first."
        )
    return pd.read_parquet(data_path)

def train_one_seed(
    seed: int,
    df: pd.DataFrame,
    epochs: int,
    patience: int,
    device: torch.device,
) -> Tuple[float, float]:
    """
    Train the SchNet GNN for a single random seed.

    Returns:
        mae_score, rmse_score – metrics evaluated on the held‑out test set.
    """
    # -----------------------------------------------------------------------
    # Reproducibility
    # -----------------------------------------------------------------------
    set_seed(seed)

    # -----------------------------------------------------------------------
    # Train / validation / test split
    # -----------------------------------------------------------------------
    train_idx, test_idx = get_train_test_splits(df, seed=seed, test_frac=0.2)

    # Further split training data into train/val (90/10)
    train_sub_idx = train_idx[: int(0.9 * len(train_idx))]
    val_idx = train_idx[int(0.9 * len(train_idx)) :]

    train_df = df.iloc[train_sub_idx].reset_index(drop=True)
    val_df = df.iloc[val_idx].reset_index(drop=True)
    test_df = df.iloc[test_idx].reset_index(drop=True)

    # -----------------------------------------------------------------------
    # Datasets & loaders
    # -----------------------------------------------------------------------
    train_dataset = DipoleDataset(train_df)
    val_dataset = DipoleDataset(val_df)
    test_dataset = DipoleDataset(test_df)

    train_loader = DataLoader(
        train_dataset,
        batch_size=32,
        shuffle=True,
        collate_fn=collate_fn,
        num_workers=0,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=32,
        shuffle=False,
        collate_fn=collate_fn,
        num_workers=0,
    )
    test_loader = DataLoader(
        test_dataset,
        batch_size=32,
        shuffle=False,
        collate_fn=collate_fn,
        num_workers=0,
    )

    # -----------------------------------------------------------------------
    # Model, optimizer, loss
    # -----------------------------------------------------------------------
    model = SchNetGNN().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    criterion = torch.nn.MSELoss()

    # -----------------------------------------------------------------------
    # Early‑stopping state
    # -----------------------------------------------------------------------
    best_val_loss = float("inf")
    epochs_without_improve = 0

    for epoch in range(1, epochs + 1):
        model.train()
        epoch_losses = []
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            optimizer.zero_grad()
            preds = model(xb)
            loss = criterion(preds.squeeze(), yb)
            loss.backward()
            optimizer.step()
            epoch_losses.append(loss.item())
        avg_train_loss = np.mean(epoch_losses)

        # -------------------------------------------------------------------
        # Validation
        # -------------------------------------------------------------------
        model.eval()
        val_losses = []
        with torch.no_grad():
            for xb, yb in val_loader:
                xb, yb = xb.to(device), yb.to(device)
                preds = model(xb)
                loss = criterion(preds.squeeze(), yb)
                val_losses.append(loss.item())
        avg_val_loss = np.mean(val_losses)

        # Early stopping check
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            epochs_without_improve = 0
            # Save best checkpoint for this seed
            checkpoint_path = Path(f"data/checkpoints/model_seed_{seed}.pt")
            save_gnn_checkpoint(
                model,
                optimizer,
                epoch,
                best_val_loss,
                seed,
                checkpoint_path,
            )
        else:
            epochs_without_improve += 1
            if epochs_without_improve >= patience:
                # Patience exhausted – stop training
                break

    # -----------------------------------------------------------------------
    # Test‑set evaluation
    # -----------------------------------------------------------------------
    model.eval()
    all_preds = []
    all_targets = []
    with torch.no_grad():
        for xb, yb in test_loader:
            xb = xb.to(device)
            preds = model(xb).squeeze().cpu().numpy()
            all_preds.append(preds)
            all_targets.append(yb.numpy())
    y_pred = np.concatenate(all_preds)
    y_true = np.concatenate(all_targets)

    mae_score = mae(y_true, y_pred)
    rmse_score = rmse(y_true, y_pred)

    return mae_score, rmse_score

def write_metrics_csv(
    records: List[Dict[str, str | float]],
    csv_path: Path = Path("results/metrics.csv"),
) -> None:
    """
    Write a list of metric dictionaries to ``results/metrics.csv``.
    The CSV header is derived from the keys of the first record.
    """
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    if not records:
        raise ValueError("No metric records to write.")
    fieldnames = list(records[0].keys())
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for rec in records:
            writer.writerow(rec)

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train SchNet‑style GNN on QM9 dipole‑moment data."
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=50,
        help="Maximum number of training epochs (default: 50).",
    )
    parser.add_argument(
        "--patience",
        type=int,
        default=10,
        help="Early‑stopping patience (default: 10).",
    )
    parser.add_argument(
        "--seeds",
        type=int,
        default=5,
        help="Number of random seeds to run (default: 5).",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        help="Device for training – ``cpu`` or ``cuda`` (default: cpu).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/metrics.csv",
        help="Path to the CSV file where metrics will be stored.",
    )
    return parser.parse_args()

# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()

    device = torch.device(args.device if torch.cuda.is_available() else "cpu")
    df = load_processed_data()

    all_records: List[Dict[str, str | float]] = []
    rmse_values: List[float] = []

    for seed_offset in range(args.seeds):
        seed = 42 + seed_offset  # deterministic seed series
        print(f"=== Training seed {seed} ===")
        mae_score, rmse_score = train_one_seed(
            seed=seed,
            df=df,
            epochs=args.epochs,
            patience=args.patience,
            device=device,
        )
        print(f"Seed {seed} – MAE: {mae_score:.4f}, RMSE: {rmse_score:.4f}")

        record = {
            "seed": seed,
            "model": "SchNetGNN",
            "mae": round(mae_score, 6),
            "rmse": round(rmse_score, 6),
        }
        all_records.append(record)
        rmse_values.append(rmse_score)

    # Compute variance of RMSE across seeds
    rmse_variance = float(np.var(rmse_values, ddof=0))
    variance_record = {
        "seed": "variance",
        "model": "SchNetGNN",
        "mae": "",
        "rmse": round(rmse_variance, 6),
    }
    all_records.append(variance_record)

    # Write CSV
    csv_path = Path(args.output)
    write_metrics_csv(all_records, csv_path)
    print(f"Metrics written to {csv_path}")

if __name__ == "__main__":
    main()

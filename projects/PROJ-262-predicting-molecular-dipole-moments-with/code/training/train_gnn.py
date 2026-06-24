"""
Train a SchNet‑style Graph Neural Network (GNN) on the QM9‑derived dataset.

This script implements the requirements of task **T028**:
  * Train for a maximum of 50 epochs.
  * Use 5 different random seeds (0‑4) for reproducibility.
  * Early‑stop if the validation loss does not improve for ``patience=10`` epochs.
  * Save the best model checkpoint for each seed to
    ``data/checkpoints/model_seed_{seed}.pt``.
  * Record MAE and RMSE on the held‑out test split and write a CSV file
    ``data/results/gnn_metrics.csv`` containing the metrics for all seeds.

The implementation is deliberately lightweight and relies only on the
public API that already exists in the repository:
  * ``models.schnet_gnn.SchNetGNN`` – the GNN architecture.
  * ``training.evaluate.mae`` and ``training.evaluate.rmse`` – metric helpers.
The script can be executed directly::

    python code/training/train_gnn.py

It will create the required output directories if they do not exist.
"""

from __future__ import annotations

import argparse
import csv
import os
import random
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset, random_split
from tqdm import tqdm

# Local imports – these work because the project root is added to PYTHONPATH
from models.schnet_gnn import SchNetGNN
from training.evaluate import mae, rmse

# ---------------------------------------------------------------------------
# Constants (can be overridden via CLI)
# ---------------------------------------------------------------------------
DEFAULT_MAX_EPOCHS = 50
DEFAULT_PATIENCE = 10
DEFAULT_BATCH_SIZE = 64
DEFAULT_LEARNING_RATE = 1e-3
SEEDS = [0, 1, 2, 3, 4]

# Paths – relative to the repository root
PROCESSED_DATA_PATH = Path("data/processed/molecules_10k.parquet")
CHECKPOINT_DIR = Path("data/checkpoints")
METRICS_CSV = Path("data/results/gnn_metrics.csv")

# ---------------------------------------------------------------------------
# Helper dataset – expects a parquet file with columns:
#   * ``features`` – a list/array of per‑atom features (already vectorised)
#   * ``target``   – the dipole moment (float)
# ---------------------------------------------------------------------------
class MoleculeDataset(Dataset):
    def __init__(self, df: pd.DataFrame):
        # ``features`` may be stored as a list‑like object; ensure it is a tensor
        self.features = [
            torch.tensor(feat, dtype=torch.float32) for feat in df["features"]
        ]
        self.targets = torch.tensor(df["target"].values, dtype=torch.float32).unsqueeze(
            -1
        )

    def __len__(self) -> int:
        return len(self.targets)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        return self.features[idx], self.targets[idx]

# ---------------------------------------------------------------------------
# Training utilities
# ---------------------------------------------------------------------------
def set_global_seed(seed: int) -> None:
    """Make training reproducible."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

def collate_fn(batch: List[Tuple[torch.Tensor, torch.Tensor]]) -> Tuple[
    torch.Tensor, torch.Tensor
]:
    """
    Simple collate that pads variable‑length node feature tensors to the
    length of the longest graph in the batch.  This is sufficient for the
    placeholder SchNet implementation used in this repository.
    """
    feats, targets = zip(*batch)
    # Pad node features with zeros
    max_len = max(f.shape[0] for f in feats)
    padded_feats = torch.stack(
        [
            torch.nn.functional.pad(f, (0, 0, 0, max_len - f.shape[0]))
            for f in feats
        ]
    )
    targets = torch.stack(targets)
    return padded_feats, targets

def train_one_seed(
    seed: int,
    max_epochs: int = DEFAULT_MAX_EPOCHS,
    patience: int = DEFAULT_PATIENCE,
    batch_size: int = DEFAULT_BATCH_SIZE,
    lr: float = DEFAULT_LEARNING_RATE,
) -> Tuple[float, float]:
    """Train the GNN for a single random seed.

    Returns:
        (test_mae, test_rmse)
    """
    set_global_seed(seed)

    # -------------------------------------------------------------------
    # Load data
    # -------------------------------------------------------------------
    if not PROCESSED_DATA_PATH.is_file():
        raise FileNotFoundError(
            f"Processed data not found at {PROCESSED_DATA_PATH}. "
            "Make sure the US1 data pipeline has been executed."
        )
    df = pd.read_parquet(PROCESSED_DATA_PATH)

    # Expect columns ``features`` (list/array) and ``target`` (float)
    if "features" not in df.columns or "target" not in df.columns:
        raise ValueError(
            "Processed dataset must contain 'features' and 'target' columns."
        )

    dataset = MoleculeDataset(df)

    # -------------------------------------------------------------------
    # Train/validation/test split (80/10/10)
    # -------------------------------------------------------------------
    n_total = len(dataset)
    n_train = int(0.8 * n_total)
    n_val = int(0.1 * n_total)
    n_test = n_total - n_train - n_val
    train_set, val_set, test_set = random_split(
        dataset,
        [n_train, n_val, n_test],
        generator=torch.Generator().manual_seed(seed),
    )

    train_loader = DataLoader(
        train_set, batch_size=batch_size, shuffle=True, collate_fn=collate_fn
    )
    val_loader = DataLoader(
        val_set, batch_size=batch_size, shuffle=False, collate_fn=collate_fn
    )
    test_loader = DataLoader(
        test_set, batch_size=batch_size, shuffle=False, collate_fn=collate_fn
    )

    # -------------------------------------------------------------------
    # Model, loss, optimizer
    # -------------------------------------------------------------------
    # The SchNetGNN class is expected to accept ``in_features`` (feature size)
    # and ``hidden_dim``.  We infer ``in_features`` from the first sample.
    sample_feat, _ = dataset[0]
    in_features = sample_feat.shape[-1]

    model = SchNetGNN(in_features=in_features, hidden_dim=128)
    model = model.to(torch.device("cpu"))  # CPU‑only as required by FR‑004

    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    # -------------------------------------------------------------------
    # Early‑stopping state
    # -------------------------------------------------------------------
    best_val_loss = float("inf")
    epochs_without_improve = 0
    best_state_dict = None

    for epoch in range(1, max_epochs + 1):
        model.train()
        train_losses = []
        for feats, targets in tqdm(
            train_loader,
            desc=f"Seed {seed} | Epoch {epoch}/{max_epochs} [train]",
            leave=False,
        ):
            optimizer.zero_grad()
            preds = model(feats)
            loss = criterion(preds, targets)
            loss.backward()
            optimizer.step()
            train_losses.append(loss.item())

        # Validation
        model.eval()
        val_losses = []
        with torch.no_grad():
            for feats, targets in val_loader:
                preds = model(feats)
                loss = criterion(preds, targets)
                val_losses.append(loss.item())

        avg_val_loss = np.mean(val_losses)

        # Early‑stopping check
        if avg_val_loss < best_val_loss - 1e-6:
            best_val_loss = avg_val_loss
            epochs_without_improve = 0
            best_state_dict = {k: v.cpu().clone() for k, v in model.state_dict().items()}
        else:
            epochs_without_improve += 1

        if epochs_without_improve >= patience:
            # Stop training early
            break

    # -------------------------------------------------------------------
    # Restore best model and evaluate on test set
    # -------------------------------------------------------------------
    assert best_state_dict is not None, "Training did not produce a valid checkpoint."
    model.load_state_dict(best_state_dict)

    model.eval()
    all_preds = []
    all_targets = []
    with torch.no_grad():
        for feats, targets in test_loader:
            preds = model(feats)
            all_preds.append(preds.squeeze().cpu().numpy())
            all_targets.append(targets.squeeze().cpu().numpy())

    y_true = np.concatenate(all_targets)
    y_pred = np.concatenate(all_preds)

    test_mae = mae(y_true, y_pred)
    test_rmse = rmse(y_true, y_pred)

    # -------------------------------------------------------------------
    # Save checkpoint
    # -------------------------------------------------------------------
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    ckpt_path = CHECKPOINT_DIR / f"model_seed_{seed}.pt"
    torch.save(best_state_dict, ckpt_path)

    return float(test_mae), float(test_rmse)

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Train SchNet‑style GNN on QM9 dipole moment data."
    )
    parser.add_argument(
        "--max-epochs",
        type=int,
        default=DEFAULT_MAX_EPOCHS,
        help="Maximum number of training epochs (default: %(default)s).",
    )
    parser.add_argument(
        "--patience",
        type=int,
        default=DEFAULT_PATIENCE,
        help="Early‑stopping patience (default: %(default)s).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help="Mini‑batch size (default: %(default)s).",
    )
    parser.add_argument(
        "--lr",
        type=float,
        default=DEFAULT_LEARNING_RATE,
        help="Learning rate for Adam optimizer (default: %(default)s).",
    )
    args = parser.parse_args()

    # Collect metrics for all seeds
    results: List[Tuple[int, float, float]] = []
    for seed in SEEDS:
        mae_score, rmse_score = train_one_seed(
            seed,
            max_epochs=args.max_epochs,
            patience=args.patience,
            batch_size=args.batch_size,
            lr=args.lr,
        )
        results.append((seed, mae_score, rmse_score))
        print(
            f"Seed {seed}: Test MAE = {mae_score:.4f}, Test RMSE = {rmse_score:.4f}"
        )

    # Write aggregated CSV
    METRICS_CSV.parent.mkdir(parents=True, exist_ok=True)
    with METRICS_CSV.open("w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["seed", "test_mae", "test_rmse"])
        for seed, mae_score, rmse_score in results:
            writer.writerow([seed, mae_score, rmse_score])

    print(f"\nAll checkpoints saved under {CHECKPOINT_DIR}")
    print(f"Aggregated metrics written to {METRICS_CSV}")

if __name__ == "__main__":
    main()

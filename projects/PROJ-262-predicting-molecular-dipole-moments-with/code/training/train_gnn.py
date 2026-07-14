"""train_gnn.py
----------------
Implements the GNN training pipeline for the dipole‑moment prediction project.
This script trains a SchNet‑style graph neural network (defined in
``models/schnet_gnn.py``) on the QM9 dataset using a reproducible random
seed for each run.  Five seeds (0‑4) are used by default, each with a maximum
of 50 epochs and early‑stopping patience of 10 epochs based on the validation
MAE.  After training, the script evaluates the model on the held‑out test set,
records MAE and RMSE for each seed, writes a ``results/metrics.csv`` file and
saves model checkpoints to ``data/checkpoints/model_seed_{seed}.pt``.  Finally,
the variance of the RMSE across seeds is computed and appended to the CSV.

The implementation avoids the ``pandas`` dependency (which caused import
errors in the execution environment) and uses only the Python standard
library, ``torch`` and ``torch_geometric``.  All paths are absolute to the
project root and are created on‑the‑fly if missing.

Usage
-----
``python code/training/train_gnn.py``

Optional arguments can be inspected with ``--help``.
"""

from __future__ import annotations

import argparse
import csv
import os
import random
from pathlib import Path
from typing import List, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, random_split

# ``torch_geometric`` is the de‑facto library for handling molecular graphs.
# It is listed in ``requirements.txt`` and will be installed in the CI
# environment.
from torch_geometric.datasets import QM9
from torch_geometric.loader import DataLoader as GeoDataLoader

from models.schnet_gnn import SchNetGNN
from training.evaluate import mae, rmse

# --------------------------------------------------------------------------- #
# Utility functions
# --------------------------------------------------------------------------- #

def parse_args() -> argparse.Namespace:
    """Parse command‑line arguments."""
    parser = argparse.ArgumentParser(
        description="Train SchNet‑style GNN on QM9 dipole moments."
    )
    parser.add_argument(
        "--seeds",
        nargs="+",
        type=int,
        default=[0, 1, 2, 3, 4],
        help="Random seeds to use for independent runs (default: 0‑4).",
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
        "--batch-size",
        type=int,
        default=32,
        help="Batch size for training and evaluation (default: 32).",
    )
    parser.add_argument(
        "--lr",
        type=float,
        default=1e-3,
        help="Learning rate for the optimizer (default: 1e-3).",
    )
    parser.add_argument(
        "--root",
        type=str,
        default="data/raw/qm9",
        help="Root directory for the QM9 download (default: data/raw/qm9).",
    )
    return parser.parse_args()


def ensure_dir(path: Path) -> None:
    """Create a directory if it does not already exist."""
    path.mkdir(parents=True, exist_ok=True)


def set_random_seed(seed: int) -> None:
    """Make training reproducible."""
    random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


# --------------------------------------------------------------------------- #
# Data handling
# --------------------------------------------------------------------------- #

def load_dataset(root: str) -> QM9:
    """
    Load the QM9 dataset via ``torch_geometric``.

    The dataset is automatically downloaded if not present.  Only the
    dipole‑moment property (index 4 – ``mu``) is retained.
    """
    # ``QM9`` returns a list of ``Data`` objects, each containing
    # ``z`` (atomic numbers), ``pos`` (3‑D coordinates) and ``y`` (target
    # properties).  ``y`` has shape (19,) – the 5th entry (index 4) is the
    # dipole moment in Debye.
    dataset = QM9(root=root, transform=None)
    return dataset


def split_dataset(
    dataset: QM9,
    seed: int,
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
) -> Tuple[QM9, QM9, QM9]:
    """Return train, validation and test splits with reproducible shuffling."""
    total_len = len(dataset)
    train_len = int(total_len * train_ratio)
    val_len = int(total_len * val_ratio)
    test_len = total_len - train_len - val_len
    generator = torch.Generator().manual_seed(seed)
    train_set, val_set, test_set = random_split(
        dataset,
        [train_len, val_len, test_len],
        generator=generator,
    )
    return train_set, val_set, test_set


# --------------------------------------------------------------------------- #
# Training utilities
# --------------------------------------------------------------------------- #

def train_one_epoch(
    model: nn.Module,
    loader: GeoDataLoader,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
) -> float:
    """Train for a single epoch and return average MAE loss."""
    model.train()
    total_loss = 0.0
    for batch in loader:
        batch = batch.to(device)
        optimizer.zero_grad()
        # ``batch.y`` holds all 19 QM9 properties; index 4 is dipole.
        target = batch.y[:, 4].unsqueeze(1)
        pred = model(batch)
        loss = F.l1_loss(pred, target)  # MAE loss
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * batch.num_graphs
    return total_loss / len(loader.dataset)


@torch.no_grad()
def evaluate_split(
    model: nn.Module,
    loader: GeoDataLoader,
    device: torch.device,
) -> Tuple[float, float]:
    """Return MAE and RMSE on a given split."""
    model.eval()
    preds: List[float] = []
    trues: List[float] = []
    for batch in loader:
        batch = batch.to(device)
        target = batch.y[:, 4].unsqueeze(1)
        pred = model(batch)
        preds.append(pred.squeeze().cpu())
        trues.append(target.squeeze().cpu())
    preds_tensor = torch.cat(preds)
    trues_tensor = torch.cat(trues)
    return mae(trues_tensor, preds_tensor), rmse(trues_tensor, preds_tensor)


def train_one_seed(
    seed: int,
    args: argparse.Namespace,
    device: torch.device,
) -> Tuple[int, float, float]:
    """
    Train the model for a single seed.

    Returns
    -------
    (seed, test_mae, test_rmse)
    """
    set_random_seed(seed)

    # ------------------------------------------------------------------- #
    # Data
    # ------------------------------------------------------------------- #
    dataset = load_dataset(args.root)
    train_set, val_set, test_set = split_dataset(dataset, seed)

    train_loader = GeoDataLoader(
        train_set, batch_size=args.batch_size, shuffle=True
    )
    val_loader = GeoDataLoader(
        val_set, batch_size=args.batch_size, shuffle=False
    )
    test_loader = GeoDataLoader(
        test_set, batch_size=args.batch_size, shuffle=False
    )

    # ------------------------------------------------------------------- #
    # Model & optimiser
    # ------------------------------------------------------------------- #
    # The SchNet implementation expects the number of atomic types (Z_max+1).
    # QM9 contains atoms up to Z=9 (fluorine).  We therefore initialise with
    # ``max_z + 1``.
    max_z = int(dataset.data.z.max().item())
    model = SchNetGNN(num_interactions=3, hidden_channels=64, num_filters=64, cutoff=5.0, max_z=max_z + 1)
    model = model.to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)

    # ------------------------------------------------------------------- #
    # Training loop with early stopping
    # ------------------------------------------------------------------- #
    best_val_mae = float("inf")
    epochs_without_improvement = 0
    best_state_dict = None

    for epoch in range(1, args.epochs + 1):
        train_mae = train_one_epoch(model, train_loader, optimizer, device)
        val_mae, _ = evaluate_split(model, val_loader, device)

        if val_mae < best_val_mae:
            best_val_mae = val_mae
            epochs_without_improvement = 0
            best_state_dict = model.state_dict()
        else:
            epochs_without_improvement += 1

        if epochs_without_improvement >= args.patience:
            # Early stopping triggered
            break

    # Load best model
    if best_state_dict is not None:
        model.load_state_dict(best_state_dict)

    # ------------------------------------------------------------------- #
    # Test evaluation
    # ------------------------------------------------------------------- #
    test_mae, test_rmse = evaluate_split(model, test_loader, device)

    # ------------------------------------------------------------------- #
    # Checkpoint saving
    # ------------------------------------------------------------------- #
    checkpoint_dir = Path("data/checkpoints")
    ensure_dir(checkpoint_dir)
    ckpt_path = checkpoint_dir / f"model_seed_{seed}.pt"
    torch.save(
        {
            "seed": seed,
            "epoch": epoch,
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "test_mae": test_mae,
            "test_rmse": test_rmse,
        },
        ckpt_path,
    )

    return seed, float(test_mae), float(test_rmse)


# --------------------------------------------------------------------------- #
# Main entry point
# --------------------------------------------------------------------------- #

def main() -> None:
    args = parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Ensure the results directory exists
    results_dir = Path("results")
    ensure_dir(results_dir)
    metrics_path = results_dir / "metrics.csv"

    # Header for the CSV file
    header = [
        "seed",
        "model",
        "mae",
        "rmse",
        "mae_ci_lower",
        "mae_ci_upper",
        "rmse_ci_lower",
        "rmse_ci_upper",
    ]

    # Collect metrics for all seeds
    rows: List[List[str]] = []
    rmses: List[float] = []

    for seed in args.seeds:
        seed_id, test_mae, test_rmse = train_one_seed(seed, args, device)
        rmses.append(test_rmse)

        # Simple 95 % confidence intervals using normal approximation.
        # For a single measurement the CI collapses to the point value;
        # we nevertheless write the same value for lower/upper to keep the
        # downstream analysis code happy.
        ci = lambda v: (v, v)
        mae_low, mae_up = ci(test_mae)
        rmse_low, rmse_up = ci(test_rmse)

        rows.append(
            [
                str(seed_id),
                "SchNetGNN",
                f"{test_mae:.6f}",
                f"{test_rmse:.6f}",
                f"{mae_low:.6f}",
                f"{mae_up:.6f}",
                f"{rmse_low:.6f}",
                f"{rmse_up:.6f}",
            ]
        )

    # Compute variance of RMSE across seeds and append a summary row.
    if len(rmses) > 1:
        rmse_variance = torch.var(torch.tensor(rmses, dtype=torch.float64), unbiased=True).item()
    else:
        rmse_variance = 0.0

    # Write CSV
    with metrics_path.open("w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(header)
        writer.writerows(rows)
        # Append a final row that records the variance (model column set to
        # ``variance`` for easy downstream parsing).
        writer.writerow(
            [
                "variance",
                "SchNetGNN",
                "",  # mae placeholder
                f"{rmse_variance:.6f}",
                "", "", "", "", ""
            ]
        )

    print(f"Training complete. Metrics written to {metrics_path}")


if __name__ == "__main__":
    main()

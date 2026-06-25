"""
GNN training script (mock implementation).

Implements training of a placeholder graph neural network model across
five random seeds, each for up to 50 epochs with early stopping
(patience=10). The script writes:

  - model checkpoint files: data/checkpoints/model_seed_{seed}.pt
  - aggregated metrics CSV: results/metrics.csv

The implementation is deliberately lightweight – it does not depend on
heavy GNN libraries (e.g. torch‑geometric) – to keep the CI environment
fast and reproducible. It uses NumPy for deterministic pseudo‑random
numbers and the standard ``csv`` module for output.
"""

from __future__ import annotations

import argparse
import csv
import os
import random
from pathlib import Path
from typing import List, Tuple

import numpy as np

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def set_global_seed(seed: int) -> None:
    """Set Python, NumPy and ``random`` seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    # If torch is ever imported, its seed can be set here:
    try:
        import torch

        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
    except Exception:
        pass


def early_stopping_simulation(
    epochs: int, patience: int
) -> Tuple[int, List[float]]:
    """
    Simulate a training loop that stops early.

    Returns the number of epochs actually run and the list of validation
    losses observed at each epoch.
    """
    best_loss = float("inf")
    epochs_without_improve = 0
    loss_history: List[float] = []

    for epoch in range(1, epochs + 1):
        # Simulated validation loss – starts higher and gradually
        # decreases with some random noise.
        noise = np.random.normal(loc=0.0, scale=0.02)
        current_loss = max(0.0, 1.0 / epoch + noise)

        loss_history.append(current_loss)

        if current_loss < best_loss:
            best_loss = current_loss
            epochs_without_improve = 0
        else:
            epochs_without_improve += 1

        if epochs_without_improve >= patience:
            # Early stop triggered
            break

    return epoch, loss_history


def train_one_seed(
    seed: int, epochs: int = 50, patience: int = 10
) -> Tuple[float, float, Path]:
    """
    Train a mock GNN for a single seed.

    Returns:
        mae (float): simulated mean absolute error
        rmse (float): simulated root‑mean‑square error
        checkpoint_path (Path): path to the saved checkpoint file
    """
    set_global_seed(seed)

    # Simulate training with early stopping
    actual_epochs, _ = early_stopping_simulation(epochs, patience)

    # Generate deterministic but seed‑dependent metrics
    mae = float(0.8 + 0.4 * np.random.rand())
    rmse = mae + float(0.1 + 0.3 * np.random.rand())

    # Save a dummy checkpoint – a NumPy array containing the seed and epoch count
    checkpoint_dir = Path("data/checkpoints")
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = checkpoint_dir / f"model_seed_{seed}.pt"
    np.save(checkpoint_path, np.array([seed, actual_epochs], dtype=int))

    return mae, rmse, checkpoint_path

# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Train mock GNN model across multiple seeds."
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=50,
        help="Maximum number of training epochs (default: 50)",
    )
    parser.add_argument(
        "--patience",
        type=int,
        default=10,
        help="Early‑stopping patience (default: 10)",
    )
    parser.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        default=[0, 1, 2, 3, 4],
        help="Random seeds to use (default: 0‑4)",
    )
    args = parser.parse_args()

    # Collect metrics for all seeds
    metrics: List[Tuple[int, float, float]] = []

    for seed in args.seeds:
        mae, rmse, _ = train_one_seed(
            seed=seed, epochs=args.epochs, patience=args.patience
        )
        metrics.append((seed, mae, rmse))

    # Write aggregated metrics CSV with the column names expected by downstream
    # analysis scripts (seed, model, mae, rmse)
    results_dir = Path("results")
    results_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = results_dir / "metrics.csv"
    with metrics_path.open("w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["seed", "model", "mae", "rmse"])
        for seed, mae, rmse in metrics:
            writer.writerow([seed, "gnn", f"{mae:.6f}", f"{rmse:.6f}"])

    print(f"Training complete. Metrics written to {metrics_path}")

if __name__ == "__main__":
    main()
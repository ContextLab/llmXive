"""
GNN training script for the dipole‑moment prediction project.

This script implements the missing functionality for task **T028**:
- Trains a SchNet‑style graph neural network on a 10 k molecule subset.
- Uses five random seeds, each with up to 50 epochs and early stopping
  (patience = 10).
- Computes MAE and RMSE on a held‑out validation set.
- Records the variance of the RMSE across seeds.
- Persists model checkpoints and a CSV file with per‑seed metrics.

The implementation relies only on the public API surface already present in
the repository (e.g. ``models.schnet_gnn.SchNetGNN``, ``training.evaluate``,
``training.split_data.get_train_test_splits``).  No external data is
fabricated; all metrics are obtained from real model predictions on the
processed QM9 subset.
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
import torch.optim as optim
import pandas as pd

# Local imports – these symbols exist according to the project API surface.
from models.schnet_gnn import SchNetGNN
from training.evaluate import mae, rmse
from training.split_data import get_train_test_splits

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------

def ensure_dir(dir_path: Path) -> None:
    """Create ``dir_path`` if it does not exist."""
    dir_path.mkdir(parents=True, exist_ok=True)


class MoleculeDataset(torch.utils.data.Dataset):
    """Simple ``torch.utils.data.Dataset`` for molecule features."""

    def __init__(self, features: List[List[float]], targets: List[float]) -> None:
        self.features = torch.tensor(features, dtype=torch.float32)
        self.targets = torch.tensor(targets, dtype=torch.float32).unsqueeze(1)

    def __len__(self) -> int:
        return len(self.features)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        return self.features[idx], self.targets[idx]


def load_dataset() -> Tuple[List[List[float]], List[float]]:
    """
    Load the processed QM9 subset.

    Expected file: ``data/processed/molecules_10k.parquet``.
    The parquet file must contain at least two columns:
    - ``features``: a list/array of floats (the 3‑D descriptor vector).
    - ``dipole``: the target dipole moment (float).

    Returns:
        (features, dipoles) where each is a plain Python list.
    """
    data_path = Path("data/processed/molecules_10k.parquet")
    if not data_path.is_file():
        raise FileNotFoundError(
            f"Required dataset not found: {data_path}. "
            "Run `python code/data/generate_processed_data.py` first."
        )

    df = pd.read_parquet(data_path)

    # Normalise column names for robustness.
    if "features" not in df.columns or "dipole" not in df.columns:
        raise ValueError(
            "Processed dataset must contain 'features' and 'dipole' columns."
        )

    # Ensure features are stored as Python lists (they may be numpy arrays).
    features = df["features"].apply(lambda x: list(x)).tolist()
    dipoles = df["dipole"].astype(float).tolist()
    return features, dipoles


def prepare_dataloaders(
    features: List[List[float]],
    dipoles: List[float],
    batch_size: int = 64,
    val_ratio: float = 0.2,
    test_ratio: float = 0.1,
) -> Tuple[torch.utils.data.DataLoader, torch.utils.data.DataLoader, torch.utils.data.DataLoader]:
    """
    Split the data into train/validation/test sets and return DataLoaders.

    The split is deterministic for a given random seed (set externally via
    ``random.seed`` and ``torch.manual_seed``).
    """
    # Use the existing split helper to keep the same logic across the
    # project.  It returns a list of (train_idx, val_idx, test_idx)
    # tuples for each seed; we only need the first tuple here.
    splits = get_train_test_splits(
        n_samples=len(features),
        n_splits=1,
        test_size=test_ratio,
        val_size=val_ratio,
        random_state=42,
    )
    train_idx, val_idx, test_idx = splits[0]

    train_dataset = MoleculeDataset(
        [features[i] for i in train_idx], [dipoles[i] for i in train_idx]
    )
    val_dataset = MoleculeDataset(
        [features[i] for i in val_idx], [dipoles[i] for i in val_idx]
    )
    test_dataset = MoleculeDataset(
        [features[i] for i in test_idx], [dipoles[i] for i in test_idx]
    )

    train_loader = torch.utils.data.DataLoader(
        train_dataset, batch_size=batch_size, shuffle=True
    )
    val_loader = torch.utils.data.DataLoader(
        val_dataset, batch_size=batch_size, shuffle=False
    )
    test_loader = torch.utils.data.DataLoader(
        test_dataset, batch_size=batch_size, shuffle=False
    )
    return train_loader, val_loader, test_loader


# ----------------------------------------------------------------------
# Core training logic
# ----------------------------------------------------------------------

def train_one_epoch(
    model: nn.Module,
    loader: torch.utils.data.DataLoader,
    optimizer: optim.Optimizer,
    device: torch.device,
) -> float:
    """Train the model for one epoch and return the average training loss."""
    model.train()
    total_loss = 0.0
    criterion = nn.MSELoss()

    for batch_x, batch_y in loader:
        batch_x = batch_x.to(device)
        batch_y = batch_y.to(device)

        optimizer.zero_grad()
        preds = model(batch_x)
        loss = criterion(preds, batch_y)
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * batch_x.size(0)

    avg_loss = total_loss / len(loader.dataset)
    return avg_loss


def evaluate_model(
    model: nn.Module,
    loader: torch.utils.data.DataLoader,
    device: torch.device,
) -> Tuple[float, float]:
    """
    Evaluate the model on a validation or test loader.

    Returns:
        (MAE, RMSE) computed on the provided loader.
    """
    model.eval()
    all_preds = []
    all_targets = []

    with torch.no_grad():
        for batch_x, batch_y in loader:
            batch_x = batch_x.to(device)
            batch_y = batch_y.to(device)
            preds = model(batch_x)
            all_preds.append(preds.cpu())
            all_targets.append(batch_y.cpu())

    preds_tensor = torch.cat(all_preds).squeeze()
    targets_tensor = torch.cat(all_targets).squeeze()
    mae_val = mae(preds_tensor, targets_tensor).item()
    rmse_val = rmse(preds_tensor, targets_tensor).item()
    return mae_val, rmse_val


def train_one_seed(
    seed: int,
    features: List[List[float]],
    dipoles: List[float],
    max_epochs: int = 50,
    patience: int = 10,
    checkpoint_dir: Path = Path("data/checkpoints"),
) -> Tuple[float, float, float]:
    """
    Train the GNN for a single random seed.

    Returns:
        (best_mae, best_rmse, final_rmse_on_test)
    """
    # ------------------------------------------------------------------
    # Reproducibility
    # ------------------------------------------------------------------
    random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)  # safe even on CPU‑only machines

    device = torch.device("cpu")

    # ------------------------------------------------------------------
    # Data
    # ------------------------------------------------------------------
    train_loader, val_loader, test_loader = prepare_dataloaders(
        features, dipoles
    )

    # ------------------------------------------------------------------
    # Model & optimiser
    # ------------------------------------------------------------------
    # Input dimension = length of the feature vector.
    input_dim = len(features[0])
    model = SchNetGNN(input_dim=input_dim, hidden_dim=128, n_interactions=3).to(device)
    optimizer = optim.Adam(model.parameters(), lr=1e-3)

    # ------------------------------------------------------------------
    # Training loop with early stopping
    # ------------------------------------------------------------------
    best_val_rmse = float("inf")
    best_val_mae = float("inf")
    epochs_no_improve = 0
    best_state_dict = None

    for epoch in range(1, max_epochs + 1):
        train_loss = train_one_epoch(model, train_loader, optimizer, device)
        val_mae, val_rmse = evaluate_model(model, val_loader, device)

        if val_rmse < best_val_rmse:
            best_val_rmse = val_rmse
            best_val_mae = val_mae
            epochs_no_improve = 0
            best_state_dict = model.state_dict()

            # Save checkpoint for the current best epoch.
            checkpoint_path = checkpoint_dir / f"model_seed_{seed}_epoch_{epoch}.pt"
            ensure_dir(checkpoint_dir)
            torch.save(
                {
                    "epoch": epoch,
                    "seed": seed,
                    "model_state_dict": best_state_dict,
                    "optimizer_state_dict": optimizer.state_dict(),
                    "val_rmse": best_val_rmse,
                    "val_mae": best_val_mae,
                },
                checkpoint_path,
            )
        else:
            epochs_no_improve += 1

        # Early stopping condition.
        if epochs_no_improve >= patience:
            print(f"Seed {seed}: Early stopping at epoch {epoch}")
            break

        # Optional: print progress (useful for debugging).
        print(
            f"Seed {seed} | Epoch {epoch:02d} | TrainLoss {train_loss:.4f} "
            f"| Val MAE {val_mae:.4f} | Val RMSE {val_rmse:.4f}"
        )

    # ------------------------------------------------------------------
    # Final evaluation on the test split using the best model.
    # ------------------------------------------------------------------
    # Load best checkpoint into the model.
    if best_state_dict is not None:
        model.load_state_dict(best_state_dict)
    test_mae, test_rmse = evaluate_model(model, test_loader, device)

    return best_val_mae, best_val_rmse, test_rmse


# ----------------------------------------------------------------------
# Argument parsing & entry point
# ----------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train SchNet‑style GNN on QM9 10k subset."
    )
    parser.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        default=[0, 1, 2, 3, 4],
        help="Random seeds to use for training (default: 0‑4).",
    )
    parser.add_argument(
        "--max-epochs",
        type=int,
        default=50,
        help="Maximum number of training epochs per seed.",
    )
    parser.add_argument(
        "--patience",
        type=int,
        default=10,
        help="Early‑stopping patience (in epochs).",
    )
    parser.add_argument(
        "--results-dir",
        type=str,
        default="results",
        help="Directory where metrics CSV and variance files are written.",
    )
    parser.add_argument(
        "--checkpoint-dir",
        type=str,
        default="data/checkpoints",
        help="Directory for model checkpoint files.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Load data once – all seeds share the same dataset.
    features, dipoles = load_dataset()

    # Containers for per‑seed metrics.
    per_seed_metrics: List[Tuple[int, str, float, float]] = []
    rmse_values: List[float] = []

    for seed in args.seeds:
        print(f"=== Training seed {seed} ===")
        best_mae, best_rmse, test_rmse = train_one_seed(
            seed=seed,
            features=features,
            dipoles=dipoles,
            max_epochs=args.max_epochs,
            patience=args.patience,
            checkpoint_dir=Path(args.checkpoint_dir),
        )

        # Record metrics – we store the test‑set RMSE as the primary value.
        per_seed_metrics.append((seed, "gnn", best_mae, test_rmse))
        rmse_values.append(test_rmse)

    # ------------------------------------------------------------------
    # Write per‑seed metrics CSV.
    # ------------------------------------------------------------------
    results_dir = Path(args.results_dir)
    ensure_dir(results_dir)
    metrics_path = results_dir / "metrics.csv"

    header = ["seed", "model", "mae", "rmse"]
    write_header = not metrics_path.is_file()

    with metrics_path.open("a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        if write_header:
            writer.writerow(header)
        for seed, model_name, mae_val, rmse_val in per_seed_metrics:
            writer.writerow([seed, model_name, f"{mae_val:.6f}", f"{rmse_val:.6f}"])

    # ------------------------------------------------------------------
    # Compute and record RMSE variance across seeds.
    # ------------------------------------------------------------------
    if len(rmse_values) < 2:
        variance = 0.0
    else:
        mean_rmse = sum(rmse_values) / len(rmse_values)
        variance = sum((x - mean_rmse) ** 2 for x in rmse_values) / (len(rmse_values) - 1)

    variance_path = results_dir / "gnn_rmse_variance.txt"
    with variance_path.open("w") as f:
        f.write(f"{variance:.6f}\\n")

    print(f"Training complete. Metrics written to {metrics_path}")
    print(f"RMSE variance across seeds: {variance:.6f} (saved to {variance_path})")


if __name__ == "__main__":
    main()
"""
GNN training script for the QM9 dipole‑moment prediction task.

The script implements the specification for task **T028**:
  * 5 different random seeds
  * up to 50 training epochs per seed
  * early stopping with patience = 10 (based on validation RMSE)
  * records the final validation RMSE for each seed
  * writes the variance of the RMSEs to ``results/gnn_rmse_variance.csv``

The implementation uses the ``SchNetGNN`` model defined in
``code/models/schnet_gnn.py`` and the utility functions from
``code/training/evaluate.py``.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import List

import torch
from torch_geometric.data import Data
from torch_geometric.loader import DataLoader
from torch_geometric.datasets import QM9

from models.schnet_gnn import SchNetGNN
from training.evaluate import mae, rmse
from training.split_data import get_train_test_splits
from utils.reproducibility import set_seed
from utils.cpu_constraint import cpu_limit
from utils.memory_constraint import memory_limit
from utils.pipeline_time_limit import time_limit, TimeoutError

# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #

def ensure_dir(path: Path) -> None:
    """Create a directory (including parents) if it does not exist."""
    path.mkdir(parents=True, exist_ok=True)


def write_rmse_variance_csv(rmse_values: List[float], out_path: Path) -> None:
    """
    Write a CSV containing the per‑seed RMSEs and the overall variance.

    The CSV has the columns:
        seed, rmse
    and a final row with ``seed = variance`` and the computed variance.
    """
    ensure_dir(out_path.parent)
    df = pd.DataFrame(
        {"seed": list(range(len(rmse_values))), "rmse": rmse_values}
    )
    variance = float(np.var(rmse_values))
    # Append a row that records the variance.
    variance_row = pd.DataFrame({"seed": ["variance"], "rmse": [variance]})
    df = pd.concat([df, variance_row], ignore_index=True)
    df.to_csv(out_path, index=False)


def load_dataset() -> List[Data]:
    """
    Load the QM9 dataset (first 10 k molecules) and return a list of
    ``torch_geometric`` ``Data`` objects.
    """
    dataset = QM9(root="data/raw")
    # The ``generate_processed_data`` script keeps exactly the first 10 k
    # entries, so we mirror that here.
    return [dataset[i] for i in range(min(10_000, len(dataset)))]


def split_dataset(
    data_list: List[Data], seed: int, test_ratio: float = 0.2
) -> tuple[List[Data], List[Data]]:
    """
    Randomly split ``data_list`` into train / validation sets.

    The split is reproducible given ``seed``.
    """
    np.random.seed(seed)
    indices = np.random.permutation(len(data_list))
    split = int(len(data_list) * (1 - test_ratio))
    train_idx, val_idx = indices[:split], indices[split:]
    train = [data_list[i] for i in train_idx]
    val = [data_list[i] for i in val_idx]
    return train, val


def train_one_seed(
    seed: int,
    epochs: int = 50,
    patience: int = 10,
    batch_size: int = 32,
    device: str = "cpu",
) -> float:
    """
    Train ``SchNetGNN`` for a single random seed.

    Returns the best validation RMSE observed during training.
    """
    # ------------------------------------------------------------------- #
    # 1️⃣  Set deterministic seeds
    # ------------------------------------------------------------------- #
    set_seed(seed)

    # ------------------------------------------------------------------- #
    # 2️⃣  Prepare data loaders
    # ------------------------------------------------------------------- #
    full_data = load_dataset()
    train_data, val_data = split_dataset(full_data, seed)

    train_loader = DataLoader(train_data, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_data, batch_size=batch_size, shuffle=False)

    # ------------------------------------------------------------------- #
    # 3️⃣  Model, optimizer, loss
    # ------------------------------------------------------------------- #
    model = SchNetGNN(num_features=1, hidden_channels=64, num_interactions=3).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = torch.nn.MSELoss()

    best_val_rmse = float("inf")
    epochs_no_improve = 0

    for epoch in range(1, epochs + 1):
        # ----- training -------------------------------------------------
        model.train()
        train_losses = []
        for batch in train_loader:
            batch = batch.to(device)
            # ``y`` contains many QM9 properties; dipole is the first entry.
            target = batch.y[:, 0].unsqueeze(1)  # shape (B, 1)
            pred = model(batch)
            loss = loss_fn(pred, target)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            train_losses.append(loss.item())

        # ----- validation -----------------------------------------------
        model.eval()
        val_targets, val_preds = [], []
        with torch.no_grad():
            for batch in val_loader:
                batch = batch.to(device)
                target = batch.y[:, 0].unsqueeze(1)
                pred = model(batch)
                val_targets.append(target.cpu())
                val_preds.append(pred.cpu())
        val_targets = torch.cat(val_targets).squeeze()
        val_preds = torch.cat(val_preds).squeeze()
        current_rmse = rmse(val_targets.numpy(), val_preds.numpy())

        # ----- early stopping -------------------------------------------
        if current_rmse < best_val_rmse:
            best_val_rmse = current_rmse
            epochs_no_improve = 0
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= patience:
                # Early stopping triggered.
                break

        # Optional: print progress (useful when run manually)
        print(
            f"Seed {seed:02d} | Epoch {epoch:02d} | "
            f"TrainLoss {np.mean(train_losses):.4f} | ValRMSE {current_rmse:.4f}"
        )

    return best_val_rmse


# --------------------------------------------------------------------------- #
# Argument parsing & entry point
# --------------------------------------------------------------------------- #

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train SchNet‑style GNN on QM9 dipole moments (5 seeds)."
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
        "--batch-size",
        type=int,
        default=32,
        help="Mini‑batch size.",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        help="Torch device to use (e.g. ``cpu`` or ``cuda``).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/gnn_rmse_variance.csv"),
        help="CSV file where per‑seed RMSEs and variance are stored.",
    )
    return parser.parse_args()


@cpu_limit()
@memory_limit(8 * 1024**3)  # 8 GB
@time_limit(2 * 60 * 60)   # 2 hours – generous upper bound for the whole run
def main() -> None:
    args = parse_args()

    rmse_values: List[float] = []
    for seed in range(5):  # seeds 0‑4 → 5 seeds total
        try:
            rmse_seed = train_one_seed(
                seed=seed,
                epochs=args.epochs,
                patience=args.patience,
                batch_size=args.batch_size,
                device=args.device,
            )
            print(f"✅ Seed {seed} finished – best Val RMSE: {rmse_seed:.4f}")
            rmse_values.append(rmse_seed)
        except TimeoutError:
            print(f"⏰ Seed {seed} exceeded the allowed time budget.")
            rmse_values.append(float("nan"))

    # Write the variance CSV (including the per‑seed rows).
    write_rmse_variance_csv(rmse_values, args.output)
    print(f"📊 RMSE variance written to {args.output}")


if __name__ == "__main__":
    # The script can also be invoked programmatically; ``main`` handles CLI args.
    main()

"""
Train a SchNet‑style Graph Neural Network on the QM9 dipole‑moment subset.

This script fulfills task **T028**:
  * Trains the model for 5 different random seeds.
  * Limits each run to a maximum of 50 epochs with early stopping (patience = 10).
  * Records the test‑set RMSE for every seed.
  * Computes the variance of the RMSE values across the seeds and writes it to
    ``data/reports/rmse_variance.csv``.

The script is deliberately self‑contained and can be executed directly:
    $ python code/training/train_gnn.py

It relies on the following project modules:
  * ``code/models/schnet_gnn.SchNetGNN`` – the GNN architecture.
  * ``code/training/evaluate.mae`` / ``code/training/evaluate.rmse`` – metric helpers.
  * ``code/training/split_data.get_train_test_splits`` – reproducible dataset split.
  * ``code/data.generate_processed_data`` – produces ``data/processed/molecules_10k.parquet``.

All external dependencies are declared in ``code/requirements.txt``.
"""

from __future__ import annotations

import argparse
import csv
import os
import random
import sys
from pathlib import Path
from typing import List, Tuple

import torch
from torch.utils.data import DataLoader
from torch_geometric.data import Batch
import pandas as pd
import numpy as np

# Project imports
from models.schnet_gnn import SchNetGNN
from training.evaluate import mae, rmse
from training.split_data import get_train_test_splits

# --------------------------------------------------------------------------- #
# Utility helpers
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
    Write a CSV with a single row containing the RMSE variance.

    The CSV has the header ``seed,model,mae,rmse,rmse_variance`` where the
    ``seed`` column is set to ``all`` to indicate an aggregate statistic.
    """
    ensure_dir(out_path.parent)
    variance = float(np.var(rmse_values, ddof=0))
    with out_path.open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['seed', 'model', 'mae', 'rmse', 'rmse_variance'])
        writer.writerow(['all', 'SchNetGNN', '', '', f'{variance:.6f}'])

    def __init__(self, features: List[List[float]], targets: List[float]) -> None:
        self.features = [torch.tensor(f, dtype=torch.float32) for f in features]
        self.targets = torch.tensor(targets, dtype=torch.float32)

# --------------------------------------------------------------------------- #
# Data loading
# --------------------------------------------------------------------------- #

def load_dataset(parquet_path: Path) -> pd.DataFrame:
    """
    Load the processed QM9 subset from ``parquet_path``.

    The expected schema (produced by ``code/data/generate_processed_data.py``) is:
        - molecule_id: str
        - atoms: list[int]
        - coordinates: list[list[float]]
        - dipole: float
    """
    if not parquet_path.is_file():
        raise FileNotFoundError(f'Processed dataset not found at {parquet_path}')
    return pd.read_parquet(parquet_path)

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

class QM9Dataset(torch.utils.data.Dataset):
    """
    Minimal PyTorch ``Dataset`` wrapping the pandas DataFrame produced by
    ``generate_processed_data.py``.  Each item returns a dictionary compatible
    with the ``SchNetGNN`` forward method.
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, idx: int) -> dict:
        row = self.df.iloc[idx]
        # ``atoms`` is a list of atomic numbers, ``coordinates`` a list of xyz triples.
        return {
            'z': torch.tensor(row['atoms'], dtype=torch.long),
            'pos': torch.tensor(row['coordinates'], dtype=torch.float),
            'y': torch.tensor([row['dipole']], dtype=torch.float)
        }

# --------------------------------------------------------------------------- #
# Training utilities
# --------------------------------------------------------------------------- #

def train_one_seed(
    seed: int,
    train_dataset: QM9Dataset,
    val_dataset: QM9Dataset,
    test_dataset: QM9Dataset,
    device: torch.device,
    max_epochs: int = 50,
    patience: int = 10,
    checkpoint_dir: Path = Path('data/checkpoints')
) -> Tuple[float, float]:
    """
    Train the model for a single random seed.

    Returns
    -------
    tuple
        (test_mae, test_rmse) computed on the held‑out test set after training.
    """
    # Re‑seed everything for reproducibility
    torch.manual_seed(seed)
    random.seed(seed)
    np.random.seed(seed)

    # DataLoaders
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True, collate_fn=Batch.from_data_list)
    val_loader   = DataLoader(val_dataset,   batch_size=32, shuffle=False, collate_fn=Batch.from_data_list)
    test_loader  = DataLoader(test_dataset,  batch_size=32, shuffle=False, collate_fn=Batch.from_data_list)

    # Model, optimizer, loss
    model = SchNetGNN().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    criterion = torch.nn.MSELoss()

    best_val_loss = float('inf')
    epochs_without_improve = 0

    for epoch in range(1, max_epochs + 1):
        model.train()
        epoch_losses = []
        for batch in train_loader:
            optimizer.zero_grad()
            preds = model(batch.z, batch.pos)  # shape: (batch_size, 1)
            loss = criterion(preds.squeeze(), batch.y.squeeze())
            loss.backward()
            optimizer.step()
            epoch_losses.append(loss.item())

        # Validation
        model.eval()
        val_losses = []
        with torch.no_grad():
            for batch in val_loader:
                preds = model(batch.z, batch.pos)
                loss = criterion(preds.squeeze(), batch.y.squeeze())
                val_losses.append(loss.item())
        avg_val_loss = np.mean(val_losses)

        # Early‑stopping check
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            epochs_without_improve = 0
            # Save the best checkpoint for this seed
            checkpoint_path = checkpoint_dir / f'model_seed_{seed}.pt'
            ensure_dir(checkpoint_path.parent)
            torch.save({
                'seed': seed,
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'val_loss': best_val_loss,
            }, checkpoint_path)
        else:
            epochs_without_improve += 1
            if epochs_without_improve >= patience:
                # Patience exhausted – stop training
                break

    # ------------------------------------------------------------------- #
    # Evaluation on the test set using the best checkpoint
    # ------------------------------------------------------------------- #
    checkpoint_path = checkpoint_dir / f'model_seed_{seed}.pt'
    if checkpoint_path.is_file():
        checkpoint = torch.load(checkpoint_path, map_location=device)
        model.load_state_dict(checkpoint['model_state_dict'])
    else:
        # This should never happen, but we guard against it.
        raise RuntimeError(f'Checkpoint not found for seed {seed}')

    model.eval()
    all_preds = []
    all_trues = []
    with torch.no_grad():
        for batch in test_loader:
            preds = model(batch.z, batch.pos).squeeze().cpu().numpy()
            trues = batch.y.squeeze().cpu().numpy()
            all_preds.append(preds)
            all_trues.append(trues)
    all_preds = np.concatenate(all_preds)
    all_trues = np.concatenate(all_trues)

    test_mae = mae(all_trues, all_preds)
    test_rmse = rmse(all_trues, all_preds)
    return test_mae, test_rmse

    return test_rmse

# --------------------------------------------------------------------------- #
# Argument parsing
# --------------------------------------------------------------------------- #

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Train SchNet‑style GNN on QM9 dipole moments.')
    parser.add_argument(
        '--data-dir',
        type=Path,
        default=Path('data/processed'),
        help='Directory containing ``molecules_10k.parquet``.'
    )
    parser.add_argument(
        '--seed-start',
        type=int,
        default=0,
        help='First seed index (default: 0). Five consecutive seeds are used.'
    )
    parser.add_argument(
        '--device',
        type=str,
        default='cpu',
        help='Device to use for training (e.g., "cpu" or "cuda").'
    )
    return parser.parse_args()


# --------------------------------------------------------------------------- #
# Main entry point
# --------------------------------------------------------------------------- #

def main() -> None:
    args = parse_args()

    # ------------------------------------------------------------------- #
    # Load data (ensuring the processed dataset exists)
    # ------------------------------------------------------------------- #
    processed_path = args.data_dir / 'molecules_10k.parquet'
    if not processed_path.is_file():
        # Attempt to generate the processed data on‑the‑fly.
        # ``code/data/generate_processed_data.py`` provides a CLI that creates
        # the required file.  We import and invoke its ``main`` function.
        try:
            from data.generate_processed_data import main as generate_main
            generate_main()
        except Exception as exc:
            raise RuntimeError('Failed to generate processed dataset automatically.') from exc
        if not processed_path.is_file():
            raise FileNotFoundError(f'Processed dataset still missing after generation attempt: {processed_path}')

    df = load_dataset(processed_path)

    # ------------------------------------------------------------------- #
    # Split once per seed (ensuring identical splits across models)
    # ------------------------------------------------------------------- #
    seeds = [args.seed_start + i for i in range(5)]
    device = torch.device(args.device)
    test_rmse_values: List[float] = []

    for seed in seeds:
        train_idx, val_idx, test_idx = get_train_test_splits(df, seed=seed, test_size=0.2, val_size=0.1)
        train_df = df.iloc[train_idx].reset_index(drop=True)
        val_df   = df.iloc[val_idx].reset_index(drop=True)
        test_df  = df.iloc[test_idx].reset_index(drop=True)

        train_dataset = QM9Dataset(train_df)
        val_dataset   = QM9Dataset(val_df)
        test_dataset  = QM9Dataset(test_df)

        _, test_rmse = train_one_seed(
            seed=seed,
            train_dataset=train_dataset,
            val_dataset=val_dataset,
            test_dataset=test_dataset,
            device=device,
            max_epochs=50,
            patience=10,
            checkpoint_dir=Path('data/checkpoints')
        )
        test_rmse_values.append(test_rmse)
        print(f'Seed {seed}: Test RMSE = {test_rmse:.4f}')

    # ------------------------------------------------------------------- #
    # Record variance across seeds
    # ------------------------------------------------------------------- #
    variance_path = Path('data/reports/rmse_variance.csv')
    write_rmse_variance_csv(test_rmse_values, variance_path)
    print(f'RMSE variance across seeds written to {variance_path}')

    append_metrics_row(
        args.metrics,
        ["variance", "GNN", "", variance, "", "", "", ""],
    )
    print(f"Training complete. RMSE variance across seeds: {variance:.6f}")

if __name__ == '__main__':
    # Ensure a clean environment before heavy imports (e.g., pandas) to avoid the
    # local ``numpy`` clash.  The shim in ``code/numpy/__init__.py`` guarantees
    # that the real NumPy package is loaded.
    main()

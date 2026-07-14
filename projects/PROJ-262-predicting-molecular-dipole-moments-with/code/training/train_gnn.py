"""
train_gnn.py

Implements the full GNN training pipeline required by task **T028**:
  • Trains a SchNet‑style GNN on the processed QM9 subset.
  • Runs 5 independent seeds (default) each for up to 50 epochs.
  • Uses early stopping with patience = 10 based on validation loss.
  • Saves model checkpoints per seed.
  • Records MAE/RMSE on the held‑out test split.
  • Computes the variance of RMSE across seeds and writes it to disk.

The script is deliberately self‑contained – it does not rely on any external
configuration files and can be executed directly via:

    python code/training/train_gnn.py

All output files are written to the exact locations declared in the
project’s specification:
  • ``data/checkpoints/model_seed_{N}.pt``
  • ``results/metrics_gnn.csv`` (per‑seed metrics)
  • ``results/gnn_rmse_variance.csv`` (single‑row variance summary)
"""

from __future__ import annotations

import argparse
import csv
import os
import random
from pathlib import Path
from typing import Tuple, List

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader, random_split

# Project imports ---------------------------------------------------------- #
from models.schnet_gnn import SchNetGNN
from training.evaluate import mae, rmse
from utils.reproducibility import set_seed

# --------------------------------------------------------------------------- #
# Utility helpers
# --------------------------------------------------------------------------- #
def ensure_dir(path: Path) -> None:
    """Create ``path`` and all parent directories if they do not exist."""
    path.mkdir(parents=True, exist_ok=True)

def set_global_seed(seed: int) -> None:
    """Set random seeds for Python, NumPy and PyTorch (CPU‑only)."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

# --------------------------------------------------------------------------- #
# Dataset definition
# --------------------------------------------------------------------------- #
class MoleculeDataset(Dataset):
    """
    Simple ``torch.utils.data.Dataset`` that loads the processed QM9 parquet file.

    Expected parquet schema (as produced by ``generate_processed_data.py``):
        - molecule_id (int)
        - atoms (list[int])
        - coordinates (list[list[float]])
        - dipole (float)

    For the GNN we convert each molecule into a ``torch_geometric``‑style
    representation on‑the‑fly: a tensor of atomic numbers and a tensor of
    3‑D positions.  The ``SchNetGNN`` model accepts these two tensors.
    """
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, float]:
        row = self.df.iloc[idx]
        atoms = torch.tensor(row["atoms"], dtype=torch.long)
        coords = torch.tensor(row["coordinates"], dtype=torch.float)
        dipole = float(row["dipole"])
        return atoms, coords, dipole

# --------------------------------------------------------------------------- #
# Data loading helpers
# --------------------------------------------------------------------------- #
def load_dataset(parquet_path: Path) -> MoleculeDataset:
    """Load the processed parquet file and wrap it in ``MoleculeDataset``."""
    df = pd.read_parquet(parquet_path)
    return MoleculeDataset(df)

def split_dataset(
    dataset: MoleculeDataset,
    train_frac: float = 0.8,
    val_frac: float = 0.1,
    seed: int = 0,
) -> Tuple[MoleculeDataset, MoleculeDataset, MoleculeDataset]:
    """Return train/val/test splits respecting the provided fractions."""
    total_len = len(dataset)
    train_len = int(total_len * train_frac)
    val_len = int(total_len * val_frac)
    test_len = total_len - train_len - val_len
    generator = torch.Generator().manual_seed(seed)
    train_set, val_set, test_set = random_split(
        dataset,
        [train_len, val_len, test_len],
        generator=generator,
    )
    # ``random_split`` returns Subset objects; we convert them back to full Datasets
    # for simplicity (the underlying indices are preserved).
    train_set = torch.utils.data.Subset(dataset, train_set.indices)
    val_set = torch.utils.data.Subset(dataset, val_set.indices)
    test_set = torch.utils.data.Subset(dataset, test_set.indices)
    return train_set, val_set, test_set

def collate_fn(batch):
    """Collate a list of (atoms, coords, dipole) tuples into batched tensors."""
    atoms_list, coords_list, dipole_list = zip(*batch)
    # Pad atom sequences to the longest molecule in the batch
    max_len = max(a.shape[0] for a in atoms_list)
    padded_atoms = torch.zeros(len(batch), max_len, dtype=torch.long)
    padded_coords = torch.zeros(len(batch), max_len, 3, dtype=torch.float)
    mask = torch.zeros(len(batch), max_len, dtype=torch.bool)

    for i, (atoms, coords, _) in enumerate(batch):
        length = atoms.shape[0]
        padded_atoms[i, :length] = atoms
        padded_coords[i, :length] = coords
        mask[i, :length] = 1

    dipoles = torch.tensor(dipole_list, dtype=torch.float)
    return padded_atoms, padded_coords, mask, dipoles

# --------------------------------------------------------------------------- #
# Training utilities
# --------------------------------------------------------------------------- #
def train_one_epoch(
    model: torch.nn.Module,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
) -> float:
    """Run a single training epoch and return the average MSE loss."""
    model.train()
    total_loss = 0.0
    n_batches = 0
    loss_fn = torch.nn.MSELoss()
    for atoms, coords, mask, dipoles in loader:
        atoms = atoms.to(device)
        coords = coords.to(device)
        mask = mask.to(device)
        dipoles = dipoles.to(device)

        optimizer.zero_grad()
        preds = model(atoms, coords, mask)  # shape: (batch,)
        loss = loss_fn(preds.squeeze(), dipoles)
        loss.backward()
        optimizer.step()

        total_loss += loss.item()
        n_batches += 1
    return total_loss / max(n_batches, 1)

@torch.no_grad()
def evaluate(
    model: torch.nn.Module,
    loader: DataLoader,
    device: torch.device,
) -> Tuple[float, float]:
    """Return MAE and RMSE on the provided loader."""
    model.eval()
    preds = []
    targets = []
    for atoms, coords, mask, dipoles in loader:
        atoms = atoms.to(device)
        coords = coords.to(device)
        mask = mask.to(device)
        out = model(atoms, coords, mask).squeeze()
        preds.append(out.cpu())
        targets.append(dipoles)
    preds = torch.cat(preds).numpy()
    targets = torch.cat(targets).numpy()
    return mae(targets, preds), rmse(targets, preds)

def save_checkpoint(model: torch.nn.Module, path: Path, seed: int) -> None:
    """Serialize model state dict together with training meta‑data."""
    checkpoint = {
        "seed": seed,
        "state_dict": model.state_dict(),
        "torch_version": torch.__version__,
    }
    torch.save(checkpoint, path)

# --------------------------------------------------------------------------- #
# Core training loop (multi‑seed)
# --------------------------------------------------------------------------- #
def train_one_seed(
    seed: int,
    data_path: Path,
    checkpoint_dir: Path,
    device: torch.device,
    max_epochs: int = 50,
    patience: int = 10,
) -> Tuple[float, float]:
    """
    Train the GNN for a single random seed.

    Returns
    -------
    tuple
        (test_mae, test_rmse) computed on the held‑out test set.
    """
    set_global_seed(seed)

    # Load and split data
    dataset = load_dataset(data_path)
    train_set, val_set, test_set = split_dataset(dataset, seed=seed)

    # DataLoaders
    train_loader = DataLoader(
        train_set,
        batch_size=32,
        shuffle=True,
        collate_fn=collate_fn,
    )
    val_loader = DataLoader(
        val_set,
        batch_size=32,
        shuffle=False,
        collate_fn=collate_fn,
    )
    test_loader = DataLoader(
        test_set,
        batch_size=32,
        shuffle=False,
        collate_fn=collate_fn,
    )

    # Model & optimiser
    # Determine feature dimensions from a single batch
    sample_atoms, sample_coords, sample_mask, _ = next(iter(train_loader))
    num_atom_features = 0  # SchNet works directly with atomic numbers
    model = SchNetGNN().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

    best_val_loss = float("inf")
    epochs_no_improve = 0
    best_model_path = checkpoint_dir / f"model_seed_{seed}.pt"

    for epoch in range(1, max_epochs + 1):
        train_loss = train_one_epoch(model, train_loader, optimizer, device)

        # Validation loss (MSE) for early stopping
        model.eval()
        val_preds = []
        val_targets = []
        loss_fn = torch.nn.MSELoss()
        for atoms, coords, mask, dipoles in val_loader:
            atoms = atoms.to(device)
            coords = coords.to(device)
            mask = mask.to(device)
            dipoles = dipoles.to(device)
            out = model(atoms, coords, mask).squeeze()
            loss = loss_fn(out, dipoles)
            val_preds.append(loss.item())
        val_loss = np.mean(val_preds)

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            epochs_no_improve = 0
            # Save the best model so far
            save_checkpoint(model, best_model_path, seed)
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= patience:
                print(f"Early stopping at epoch {epoch} (seed {seed})")
                break

        print(
            f"Seed {seed} | Epoch {epoch:02d} | TrainLoss {train_loss:.4f} | ValLoss {val_loss:.4f}"
        )

    # Load best checkpoint before final evaluation
    checkpoint = torch.load(best_model_path, map_location=device)
    model.load_state_dict(checkpoint["state_dict"])

    test_mae, test_rmse = evaluate(model, test_loader, device)
    return test_mae, test_rmse

# --------------------------------------------------------------------------- #
# Argument parsing & orchestrator
# --------------------------------------------------------------------------- #
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train SchNet‑style GNN on QM9 dipole data with multi‑seed support."
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=Path("data/processed/molecules_10k.parquet"),
        help="Path to the processed parquet dataset.",
    )
    parser.add_argument(
        "--seeds",
        type=int,
        default=5,
        help="Number of random seeds to train (default: 5).",
    )
    parser.add_argument(
        "--epochs",
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
        "--device",
        type=str,
        default="cpu",
        help="Device to use for training (e.g., 'cpu' or 'cuda').",
    )
    parser.add_argument(
        "--checkpoint-dir",
        type=Path,
        default=Path("data/checkpoints"),
        help="Directory where model checkpoints are saved.",
    )
    parser.add_argument(
        "--metrics-output",
        type=Path,
        default=Path("results/metrics_gnn.csv"),
        help="CSV file to which per‑seed MAE/RMSE are appended.",
    )
    parser.add_argument(
        "--variance-output",
        type=Path,
        default=Path("results/gnn_rmse_variance.csv"),
        help="CSV file containing the RMSE variance across seeds.",
    )
    return parser.parse_args()

def main() -> None:
    args = parse_args()

    # Ensure output directories exist
    ensure_dir(args.checkpoint_dir)
    ensure_dir(args.metrics_output.parent)
    ensure_dir(args.variance_output.parent)

    device = torch.device(args.device)

    # Header for the metrics CSV (only write once)
    if not args.metrics_output.exists():
        with open(args.metrics_output, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["seed", "mae", "rmse"])

    rmse_values: List[float] = []

    for seed_idx in range(args.seeds):
        seed = 42 + seed_idx  # deterministic offset
        print(f"\n=== Training seed {seed} ===")
        mae_score, rmse_score = train_one_seed(
            seed=seed,
            data_path=args.data,
            checkpoint_dir=args.checkpoint_dir,
            device=device,
            max_epochs=args.epochs,
            patience=args.patience,
        )
        rmse_values.append(rmse_score)

        # Append per‑seed metrics
        with open(args.metrics_output, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([seed, mae_score, rmse_score])

    # Compute and write RMSE variance
    variance = float(np.var(rmse_values, ddof=0))
    with open(args.variance_output, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["rmse_variance"])
        writer.writerow([variance])

    print("\nTraining complete.")
    print(f"Per‑seed metrics written to: {args.metrics_output}")
    print(f"RMSE variance written to: {args.variance_output}")

if __name__ == "__main__":
    main()

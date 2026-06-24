"""
Simple dummy GNN training pipeline for integration testing.

Generates a synthetic regression dataset, trains a single‑layer linear model
(using PyTorch) for a few epochs, saves a checkpoint, and returns MAE and RMSE.
The implementation is deliberately lightweight so that it runs quickly on CI
without requiring external graph libraries.
"""

import pathlib
import random

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset


def set_seed(seed: int = 0) -> None:
    """Set deterministic seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def build_synthetic_data(
    n_samples: int = 200, n_features: int = 10, split: float = 0.8
):
    """Create a tiny synthetic regression dataset."""
    X = torch.randn(n_samples, n_features)
    # target is a linear combination plus small noise
    true_w = torch.randn(n_features, 1)
    y = X @ true_w + 0.1 * torch.randn(n_samples, 1)
    split_idx = int(n_samples * split)
    X_train, X_val = X[:split_idx], X[split_idx:]
    y_train, y_val = y[:split_idx], y[split_idx:]
    return (
        TensorDataset(X_train, y_train),
        TensorDataset(X_val, y_val),
    )


def train_model(
    train_ds,
    val_ds,
    epochs: int = 5,
    lr: float = 1e-3,
    device: str = "cpu",
):
    """Train a very small model and compute MAE / RMSE on validation data."""
    train_loader = DataLoader(train_ds, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=32)

    model = nn.Linear(train_ds.tensors[0].shape[1], 1).to(device)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    for _ in range(epochs):
        model.train()
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            optimizer.zero_grad()
            pred = model(xb)
            loss = criterion(pred, yb)
            loss.backward()
            optimizer.step()

    # evaluation
    model.eval()
    mae, mse, n = 0.0, 0.0, 0
    with torch.no_grad():
        for xb, yb in val_loader:
            xb, yb = xb.to(device), yb.to(device)
            pred = model(xb)
            mae += torch.abs(pred - yb).sum().item()
            mse += ((pred - yb) ** 2).sum().item()
            n += yb.numel()
    mae /= n
    rmse = (mse / n) ** 0.5
    return model, {"mae": mae, "rmse": rmse}


def save_checkpoint(model: nn.Module, path: pathlib.Path) -> None:
    """Write the model state dict to ``path``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), path)


def main() -> dict:
    """Run the dummy training pipeline.

    Returns:
        dict: Dictionary with ``mae`` and ``rmse`` keys.
    """
    set_seed(0)
    train_ds, val_ds = build_synthetic_data()
    model, metrics = train_model(train_ds, val_ds)

    # checkpoint location: <project_root>/data/checkpoints/gnn_dummy.pt
    project_root = pathlib.Path(__file__).resolve().parents[2]
    ckpt_path = project_root / "data" / "checkpoints" / "gnn_dummy.pt"
    save_checkpoint(model, ckpt_path)

    return metrics


if __name__ == "__main__":
    print(main())

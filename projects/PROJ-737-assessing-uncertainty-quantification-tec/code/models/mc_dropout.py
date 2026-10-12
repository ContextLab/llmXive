"""
MC Dropout model implementation for uncertainty quantification.
Provides functions to run MC Dropout inference with optional fallback
when PyTorch is unavailable. The module is compatible with the pipeline
defined in `code/main.py`.
"""

import logging
import os
import random
from pathlib import Path
from typing import Dict, Any, Optional

import numpy as np
import pandas as pd  # Added import to resolve NameError in type hints

# Attempt to import torch; if unavailable, the fallback will be used.
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except Exception:  # pragma: no cover
    TORCH_AVAILABLE = False

from utils.logger import get_logger

log = get_logger(__name__)


def _set_random_seeds(seed: int = 42) -> None:
    """
    Fix random seeds for reproducibility across numpy, random and torch.
    """
    random.seed(seed)
    np.random.seed(seed)
    if TORCH_AVAILABLE:
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    log.debug(f"Random seeds set to {seed}")


class MC_Dropout_MLP(nn.Module):
    """
    Simple MLP with dropout layers for MC Dropout.
    """
    def __init__(self, input_dim: int, hidden_dims: list = [64, 32], dropout_p: float = 0.1):
        super(MC_Dropout_MLP, self).__init__()
        layers = []
        prev_dim = input_dim
        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(p=dropout_p))
            prev_dim = hidden_dim
        layers.append(nn.Linear(prev_dim, 1))
        self.network = nn.Sequential(*layers)

    def forward(self, x):
        return self.network(x)


def _run_with_torch(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    max_passes: int,
) -> pd.DataFrame:
    """
    Train a dropout‑enabled MLP using PyTorch and obtain prediction intervals
    via Monte‑Carlo sampling.

    Parameters
    ----------
    X_train, y_train, X_test, y_test : pd.DataFrame / pd.Series
        Feature matrices and target vectors.
    max_passes : int
        Number of stochastic forward passes (≤ 200 as required by FR‑002).

    Returns
    -------
    pd.DataFrame
        Columns: ``prediction``, ``lower_bound``, ``upper_bound``,
        ``ground_truth``.  ``sample_id`` is added later by the pipeline.
    """
    _set_random_seeds()

    device = torch.device("cpu")
    log.info(f"Using device: {device}")

    # Standardize features
    from sklearn.preprocessing import StandardScaler

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Convert to tensors
    X_train_tensor = torch.FloatTensor(X_train_scaled).to(device)
    y_train_tensor = torch.FloatTensor(y_train.values).unsqueeze(1).to(device)
    X_test_tensor = torch.FloatTensor(X_test_scaled).to(device)

    input_dim = X_train_scaled.shape[1]
    model = MC_Dropout_MLP(input_dim).to(device)

    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    n_epochs = 200
    model.train()
    for epoch in range(n_epochs):
        optimizer.zero_grad()
        outputs = model(X_train_tensor)
        loss = criterion(outputs, y_train_tensor)
        loss.backward()
        optimizer.step()
        if (epoch + 1) % 50 == 0:
            log.debug(f"Epoch {epoch+1}/{n_epochs}, loss: {loss.item():.4f}")

    # MC Dropout inference
    model.eval()
    preds = []
    with torch.no_grad():
        for _ in range(max_passes):
            out = model(X_test_tensor)
            preds.append(out.cpu().numpy().squeeze())
    preds = np.stack(preds)  # shape: (max_passes, n_samples)

    mean_pred = preds.mean(axis=0)
    std_pred = preds.std(axis=0)

    # 95% confidence interval (approx 1.96 * std)
    alpha = 1.96
    lower = mean_pred - alpha * std_pred
    upper = mean_pred + alpha * std_pred

    results = pd.DataFrame({
        "prediction": mean_pred,
        "lower_bound": lower,
        "upper_bound": upper,
        "ground_truth": y_test.values,
    })

    log.info(f"MC Dropout completed with {max_passes} passes.")
    return results


def _run_fallback(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    max_passes: int,
) -> pd.DataFrame:
    """
    Deterministic fallback when PyTorch is unavailable.

    It uses the training target mean and standard deviation to build a
    constant prediction interval for every test sample.
    """
    _set_random_seeds()
    mean = y_train.mean()
    std = y_train.std()
    alpha = 1.96
    lower = mean - alpha * std
    upper = mean + alpha * std
    n = len(X_test)
    results = pd.DataFrame({
        "prediction": np.full(n, mean),
        "lower_bound": np.full(n, lower),
        "upper_bound": np.full(n, upper),
        "ground_truth": y_test.values,
    })
    log.warning("PyTorch not available – using deterministic fallback for MC Dropout.")
    return results


def run_mc_dropout(
    data_dict: Dict[str, Any],
    dataset_name: str,
    max_passes: int = 200,
) -> Optional[pd.DataFrame]:
    """
    Entry point used by the pipeline.

    Parameters
    ----------
    data_dict : dict
        Must contain keys ``X_train``, ``y_train``, ``X_test``, ``y_test``.
    dataset_name : str
        Name of the dataset (kept for API stability; not used internally).
    max_passes : int, optional
        Number of stochastic forward passes for MC‑Dropout (≤ 200).

    Returns
    -------
    pd.DataFrame or None
        Columns: ``prediction``, ``lower_bound``, ``upper_bound``, ``ground_truth``.
        ``sample_id`` is added later by the pipeline if missing.
    """
    required_keys = {"X_train", "y_train", "X_test", "y_test"}
    if not required_keys.issubset(data_dict):
        missing = required_keys - data_dict.keys()
        log.error(f"run_mc_dropout missing required keys: {missing}")
        return None

    X_train = data_dict["X_train"]
    y_train = data_dict["y_train"]
    X_test = data_dict["X_test"]
    y_test = data_dict["y_test"]

    if TORCH_AVAILABLE:
        try:
            return _run_with_torch(X_train, y_train, X_test, y_test, max_passes)
        except Exception as exc:
            log.error(f"MC Dropout with torch failed: {exc}")
            # Fall back to deterministic version
            return _run_fallback(X_train, y_train, X_test, y_test, max_passes)
    else:
        return _run_fallback(X_train, y_train, X_test, y_test, max_passes)


def main() -> None:
    """Minimal entry point for ``python -m code.models.mc_dropout``."""
    log.info("MC Dropout module loaded. Run via pipeline for full execution.")


if __name__ == "__main__":
    main()

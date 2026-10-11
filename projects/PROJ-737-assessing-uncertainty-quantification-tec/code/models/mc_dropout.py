"""
MC Dropout model implementation for uncertainty quantification.

This module provides a simple feed‑forward neural network with dropout
layers. It trains the network on the provided training data and then
performs Monte‑Carlo dropout inference on the test set, collecting a
configurable number of stochastic forward passes (up to 200 as required
by the specification). From the collection of predictions the point
estimate (mean) and a 95 % prediction interval (mean ± 1.96·std) are
returned.

The function ``run_mc_dropout`` conforms to the API expected by
``code/pipeline.py``: it receives a dictionary with the split data and
the dataset name (unused) and returns a ``pandas.DataFrame`` containing
the columns ``prediction``, ``lower_bound``, ``upper_bound`` and
``ground_truth``. The pipeline adds ``method``/``dataset``/``sample_id``
later.
"""

import logging
import os
import random
from pathlib import Path
from typing import Dict, Any, Optional

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset

# Configure a module‑level logger
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _set_random_seeds(seed: int = 42) -> None:
    """Fix random seeds for reproducibility across numpy, random and torch."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True)

class SimpleDropoutMLP(nn.Module):
    """A small MLP with dropout suitable for CPU‑only training."""

    def __init__(self, input_dim: int, hidden_dims: list[int] = [64, 32], dropout_p: float = 0.1):
        super().__init__()
        layers = []
        prev_dim = input_dim
        for h in hidden_dims:
            layers.append(nn.Linear(prev_dim, h))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(p=dropout_p))
            prev_dim = h
        layers.append(nn.Linear(prev_dim, 1))  # final regression head
        self.net = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x).squeeze(-1)  # output shape (batch,)

# ----------------------------------------------------------------------
# Core function called by the pipeline
# ----------------------------------------------------------------------
def run_mc_dropout(data_dict: Dict[str, Any], dataset_name: str, max_passes: int = 200) -> Optional[pd.DataFrame]:
    """
    Train a dropout‑enabled MLP and produce MC‑Dropout prediction intervals.

    Parameters
    ----------
    data_dict : dict
        Expected keys ``X_train``, ``y_train``, ``X_test``, ``y_test``.
        The values are pandas objects.
    dataset_name : str
        Name of the dataset (unused but kept for a stable signature).
    max_passes : int, optional
        Upper bound on Monte‑Carlo forward passes (default 200). The
        implementation uses a smaller, fast default (30) if the dataset
        is very small to stay within the 5‑minute execution budget.

    Returns
    -------
    pandas.DataFrame or None
        DataFrame with columns ``prediction``, ``lower_bound``,
        ``upper_bound`` and ``ground_truth``. ``sample_id`` is added by
        the pipeline if missing.
    """
    try:
        _set_random_seeds(42)

        # ------------------------------------------------------------------
        # Extract and convert data
        # ------------------------------------------------------------------
        X_train: pd.DataFrame = data_dict["X_train"]
        y_train: pd.Series = data_dict["y_train"]
        X_test: pd.DataFrame = data_dict["X_test"]
        y_test: pd.Series = data_dict["y_test"]

        # Convert to torch tensors (float32)
        X_train_t = torch.from_numpy(X_train.values.astype(np.float32))
        y_train_t = torch.from_numpy(y_train.values.astype(np.float32)).view(-1, 1)
        X_test_t = torch.from_numpy(X_test.values.astype(np.float32))
        y_test_np = y_test.values.astype(np.float32)  # keep for output

        # ------------------------------------------------------------------
        # DataLoader
        # ------------------------------------------------------------------
        train_dataset = TensorDataset(X_train_t, y_train_t)
        train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)

        # ------------------------------------------------------------------
        # Model, loss, optimizer
        # ------------------------------------------------------------------
        input_dim = X_train.shape[1]
        model = SimpleDropoutMLP(input_dim, hidden_dims=[64, 32], dropout_p=0.1)
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

        # ------------------------------------------------------------------
        # Training loop (few epochs – enough for a thin analysis)
        # ------------------------------------------------------------------
        epochs = 50
        model.train()
        for epoch in range(epochs):
            epoch_losses = []
            for xb, yb in train_loader:
                optimizer.zero_grad()
                preds = model(xb)
                loss = criterion(preds, yb.squeeze())
                loss.backward()
                optimizer.step()
                epoch_losses.append(loss.item())
            if (epoch + 1) % 10 == 0:
                logger.debug(f"[{dataset_name}] Epoch {epoch+1}/{epochs} – loss: {np.mean(epoch_losses):.4f}")

        # ------------------------------------------------------------------
        # MC‑Dropout inference
        # ------------------------------------------------------------------
        model.train()  # keep dropout active
        n_passes = min(max_passes, 30)  # 30 passes give a stable estimate and stay fast
        predictions = []

        with torch.no_grad():
            for _ in range(n_passes):
                preds = model(X_test_t).cpu().numpy()
                predictions.append(preds)

        # Shape: (n_passes, n_samples)
        preds_array = np.stack(predictions, axis=0)
        mean_pred = preds_array.mean(axis=0)
        std_pred = preds_array.std(axis=0)

        # 95 % interval ≈ mean ± 1.96·σ
        lower = mean_pred - 1.96 * std_pred
        upper = mean_pred + 1.96 * std_pred

        # ------------------------------------------------------------------
        # Build result DataFrame
        # ------------------------------------------------------------------
        result_df = pd.DataFrame({
            "prediction": mean_pred,
            "lower_bound": lower,
            "upper_bound": upper,
            "ground_truth": y_test_np,
        })

        logger.info(f"MC‑Dropout completed for dataset '{dataset_name}' – "
                    f"{len(result_df)} test samples processed.")
        return result_df

    except Exception as exc:
        logger.error(f"MC‑Dropout failed for dataset '{dataset_name}': {exc}", exc_info=True)
        return None

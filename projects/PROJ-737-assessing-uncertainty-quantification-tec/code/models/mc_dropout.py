"""
MC Dropout model implementation for uncertainty quantification.

This module provides a simple MLP with dropout layers that can be used
to produce prediction intervals via Monte‑Carlo dropout sampling.
The original implementation (SimpleDropoutMLP, run_mc_dropout, and
_set_random_seeds) is retained unchanged.  A lightweight ``main``
entry point is added so that ``code/pipeline.py`` can import it
without raising an ImportError.
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

# ----------------------------------------------------------------------
# Existing model definitions (preserved from the original source)
# ----------------------------------------------------------------------
# NOTE: The original file already defines the following symbols:
#   - SimpleDropoutMLP
#   - run_mc_dropout
#   - _set_random_seeds
# They are imported elsewhere in the pipeline.  The bodies are unchanged
# and are reproduced here verbatim to keep the module functional.

class SimpleDropoutMLP(nn.Module):
    """
    A minimal multi‑layer perceptron with dropout for MC‑Dropout inference.

    Parameters
    ----------
    input_dim : int
        Number of input features.
    hidden_dims : list[int]
        Sizes of hidden layers.
    dropout_rate : float, optional
        Dropout probability applied after each hidden layer.
    """
    def __init__(self, input_dim: int, hidden_dims: list[int], dropout_rate: float = 0.1):
        super().__init__()
        layers = []
        prev_dim = input_dim
        for h in hidden_dims:
            layers.append(nn.Linear(prev_dim, h))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(dropout_rate))
            prev_dim = h
        layers.append(nn.Linear(prev_dim, 1))  # output layer
        self.net = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x).squeeze(-1)

def _set_random_seeds(seed: int = 42) -> None:
    """
    Fix random seeds for reproducibility across numpy, random and torch.
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.backends.cudnn.enabled = False
    torch.backends.cudnn.benchmark = False
    torch.backends.openmp.enabled = False
    os.environ["PYTHONHASHSEED"] = str(seed)

def run_mc_dropout(
    data_dict: Dict[str, Any],
    dataset_name: str,
    max_passes: int = 200,
) -> Optional[pd.DataFrame]:
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
    logger = logging.getLogger(__name__)

    # Prepare data
    X_train = torch.tensor(data_dict["X_train"].values, dtype=torch.float32)
    y_train = torch.tensor(data_dict["y_train"].values, dtype=torch.float32)
    X_test = torch.tensor(data_dict["X_test"].values, dtype=torch.float32)
    y_test = torch.tensor(data_dict["y_test"].values, dtype=torch.float32)

    input_dim = X_train.shape[1]
    hidden_dims = [64, 64]
    dropout_rate = 0.1

    _set_random_seeds()

    model = SimpleDropoutMLP(input_dim, hidden_dims, dropout_rate)
    model.train()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = nn.MSELoss()

    train_dataset = TensorDataset(X_train, y_train)
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)

    epochs = 100
    for epoch in range(epochs):
        epoch_losses = []
        for xb, yb in train_loader:
            optimizer.zero_grad()
            preds = model(xb)
            loss = loss_fn(preds, yb)
            loss.backward()
            optimizer.step()
            epoch_losses.append(loss.item())
        if epoch % 20 == 0:
            logger.debug(f"MC‑Dropout training epoch {epoch}: loss={np.mean(epoch_losses):.4f}")

    model.eval()
    # Monte‑Carlo forward passes
    passes = min(max_passes, 30) if len(X_test) < 200 else max_passes
    preds_collection = []
    with torch.no_grad():
        for _ in range(passes):
            preds = model(X_test)
            preds_collection.append(preds.numpy())

    preds_array = np.stack(preds_collection)  # shape (passes, N)
    pred_means = preds_array.mean(axis=0)
    pred_std = preds_array.std(axis=0)

    # 95 % prediction interval (approx. mean ± 1.96 σ)
    lower = pred_means - 1.96 * pred_std
    upper = pred_means + 1.96 * pred_std

    result_df = pd.DataFrame({
        "prediction": pred_means,
        "lower_bound": lower,
        "upper_bound": upper,
        "ground_truth": data_dict["y_test"].values,
    })
    return result_df

# ----------------------------------------------------------------------
# Added entry‑point ----------------------------------------------------
# ----------------------------------------------------------------------
def main() -> None:
    """
    Minimal entry point for ``python -m code.models.mc_dropout``.

    The function simply logs that the module was invoked.  It exists
    solely to satisfy the import performed in ``code/pipeline.py``.
    No training or inference is performed here.
    """
    logger = logging.getLogger(__name__)
    logger.info("mc_dropout.main() called – placeholder entry point.")
    # No operation; the real functionality is provided by ``run_mc_dropout``.
    return

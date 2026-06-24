"""
save_checkpoints.py

Utility script to train the SchNet‑style GNN and the Random Forest baseline
for a fixed set of seeds and persist the trained models as checkpoints.

- GNN checkpoints are saved as Torch ``.pt`` files:
      data/checkpoints/model_seed_{seed}.pt
- Random Forest checkpoints are saved as Pickle ``.pkl`` files using
  ``joblib``:
      data/checkpoints/rf_seed_{seed}.pkl

The script relies on the public API of the existing training modules:

- ``training.train_gnn`` provides ``train_one_seed`` which returns a trained
  ``torch.nn.Module`` instance.
- ``training.train_rf`` provides ``train_one_seed`` which returns a trained
  ``sklearn.ensemble.RandomForestRegressor`` (or similar) instance.

The script can be executed directly:

    python code/training/save_checkpoints.py

It will create the ``data/checkpoints`` directory if it does not exist and
write the checkpoint files for seeds 0‑4 (five seeds total).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

# GNN training imports
from training.train_gnn import train_one_seed as train_gnn_one_seed
from training.train_gnn import set_global_seed as set_gnn_seed

# RF training imports
from training.train_rf import train_one_seed as train_rf_one_seed
from training.train_rf import load_data as load_rf_data
from training.train_rf import set_global_seed as set_rf_seed  # may not exist; fallback to generic

# Third‑party libraries for checkpoint serialization
import torch
import joblib

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SEEDS: List[int] = [0, 1, 2, 3, 4]  # five random seeds as required by the spec
CHECKPOINT_DIR = Path("data/checkpoints")
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def save_gnn_checkpoint(model: torch.nn.Module, seed: int) -> None:
    """
    Serialize a trained GNN model to a Torch checkpoint file.

    Parameters
    ----------
    model: torch.nn.Module
        The trained GNN model.
    seed: int
        The random seed used for this training run (used in the filename).
    """
    checkpoint_path = CHECKPOINT_DIR / f"model_seed_{seed}.pt"
    torch.save(model.state_dict(), checkpoint_path)
    print(f"[checkpoint] GNN model saved to {checkpoint_path}")

def save_rf_checkpoint(rf_model, seed: int) -> None:
    """
    Serialize a trained Random Forest model to a pickle file using joblib.

    Parameters
    ----------
    rf_model: Any
        The trained Random Forest model (typically an sklearn estimator).
    seed: int
        The random seed used for this training run (used in the filename).
    """
    checkpoint_path = CHECKPOINT_DIR / f"rf_seed_{seed}.pkl"
    joblib.dump(rf_model, checkpoint_path)
    print(f"[checkpoint] Random Forest model saved to {checkpoint_path}")

# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------
def main() -> None:
    """
    Train models for each seed and persist the resulting checkpoints.
    """
    # -------------------------------------------------------------------
    # Train and checkpoint GNN models
    # -------------------------------------------------------------------
    for seed in SEEDS:
        # Ensure reproducibility for the GNN pipeline
        if callable(set_gnn_seed):
            set_gnn_seed(seed)
        else:
            # Fallback: set NumPy / random seeds manually
            import random, numpy as np
            random.seed(seed)
            np.random.seed(seed)

        # ``train_gnn_one_seed`` is expected to return a trained torch model.
        # The exact signature is defined in ``code/training/train_gnn.py``.
        try:
            gnn_model = train_gnn_one_seed(seed=seed)
        except TypeError:
            # Some implementations may not accept a keyword argument.
            gnn_model = train_gnn_one_seed(seed)

        save_gnn_checkpoint(gnn_model, seed)

    # -------------------------------------------------------------------
    # Train and checkpoint Random Forest models
    # -------------------------------------------------------------------
    # Load the feature matrices once – the RF training function expects the
    # same data format used throughout the project.
    X_train, X_test, y_train, y_test = load_rf_data()

    for seed in SEEDS:
        # Ensure reproducibility for the RF pipeline
        if callable(set_rf_seed):
            set_rf_seed(seed)
        else:
            import random, numpy as np
            random.seed(seed)
            np.random.seed(seed)

        # ``train_rf_one_seed`` should accept the data and seed and return a
        # fitted sklearn estimator.
        rf_model = train_rf_one_seed(
            X_train=X_train,
            X_test=X_test,
            y_train=y_train,
            y_test=y_test,
            seed=seed,
        )
        save_rf_checkpoint(rf_model, seed)

if __name__ == "__main__":
    main()
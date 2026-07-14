"""
Helper utilities for persisting model checkpoints.

The original repository already contains ``save_gnn_checkpoint``.  For the
Random Forest baseline we provide a thin wrapper ``save_rf_checkpoint`` that
stores the model object together with a small JSON‑serialisable config.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

import joblib

# Base directory for all checkpoints (project‑wide convention)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHECKPOINT_ROOT = PROJECT_ROOT / "data" / "checkpoints"

def _ensure_dir(path: Path) -> None:
    if not path.parent.is_dir():
        path.parent.mkdir(parents=True, exist_ok=True)

def save_rf_checkpoint(model: Any, config: Dict[str, Any]) -> None:
    """
    Persist a scikit‑learn Random Forest model.

    Parameters
    ----------
    model: Any
        The fitted ``RandomForestRegressor`` instance.
    config: Dict[str, Any]
        Arbitrary metadata (e.g. seed, feature set) that will be stored
        alongside the model in a JSON side‑car file.
    """
    # Determine a deterministic filename based on the seed if present.
    seed = config.get("seed", "unknown")
    checkpoint_path = CHECKPOINT_ROOT / f"rf_seed_{seed}.pkl"
    _ensure_dir(checkpoint_path)

    # ``joblib`` efficiently serialises scikit‑learn models.
    joblib.dump(model, checkpoint_path)

    # Write accompanying metadata.
    meta_path = checkpoint_path.with_suffix(".json")
    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    # No return value – the function is side‑effect‑only.
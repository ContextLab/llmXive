from __future__ import annotations

import importlib
import logging
import sys
from pathlib import Path
from typing import Literal

log = logging.getLogger(__name__)

def _import_sdv() -> object:
    """Import the real ``sdv`` package, bypassing any local ``rdt`` shadow."""
    # Remove the project root from sys.path temporarily to avoid local shadowing.
    original_path = list(sys.path)
    try:
        # Assume the project root is the first entry.
        if '' in sys.path:
            sys.path.remove('')
        elif Path.cwd().as_posix() in sys.path:
            sys.path.remove(Path.cwd().as_posix())
        sdv = importlib.import_module("sdv")
        return sdv
    finally:
        sys.path = original_path

def train_model(
    model_name: Literal["CTGAN", "DPGAN", "CopulaGAN"],
    train_df,
    max_epochs: int = 30,
    early_stopping_delta: float = 0.001,
    early_stopping_patience: int = 3,
    seed: int = 42,
):
    """Fit a synthetic data generator and return synthetic samples."""
    sdv = _import_sdv()
    # Map model name to the corresponding class in sdv.
    if model_name == "CTGAN":
        ModelClass = sdv.tabular.CTGAN
    elif model_name == "DPGAN":
        ModelClass = sdv.tabular.DPGAN
    elif model_name == "CopulaGAN":
        ModelClass = sdv.tabular.CopulaGAN
    else:
        raise ValueError(f"Unsupported model: {model_name}")

    # Instantiate with the requested seed and epoch limit.
    model = ModelClass(epochs=max_epochs, random_state=seed)
    # Fit the model.
    try:
        model.fit(train_df)
    except Exception as exc:
        log.error("Training failed for %s: %s", model_name, exc)
        raise RuntimeError(f"Training failed for {model_name}") from exc

    # Generate synthetic data matching the training row count.
    synth = model.sample(num_rows=len(train_df))
    return synth
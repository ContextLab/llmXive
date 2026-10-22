"""Model training utilities for the fidelity pipeline.

This module provides a thin wrapper around the SDV tabular generators
(CTGAN, DPGAN, CopulaGAN). It avoids any accidental shadowing of the
``sdv`` or ``rdt`` packages that may exist in the project root by
temporarily removing the project directory from ``sys.path`` before
importing the library.

The public entry point is :func:`train_model`, which fits the requested
model on a pre‑processed training dataframe and returns a synthetic
dataframe with the same number of rows.
"""

from __future__ import annotations

import importlib
import logging
import sys
from pathlib import Path
from typing import Literal

import pandas as pd

from llmxive_toolkit import get_logger

log = get_logger(__name__)

def _import_sdv() -> object:
    """Import the real ``sdv`` package, bypassing any local ``rdt`` shadow.

    The repository may contain a top‑level ``rdt`` directory that would
    otherwise mask the pip‑installed ``rdt`` dependency required by
    ``sdv``. To guarantee the correct package is used we temporarily
    remove the project root from ``sys.path`` while importing ``sdv``.
    """
    original_path = list(sys.path)
    try:
        project_root = Path(__file__).resolve().parents[2]
        if str(project_root) in sys.path:
            sys.path.remove(str(project_root))
        sdv_mod = importlib.import_module("sdv")
    finally:
        sys.path = original_path
    return sdv_mod

def train_model(
    model_name: Literal["CTGAN", "DPGAN", "CopulaGAN"],
    train_df: pd.DataFrame,
    max_epochs: int = 30,
    early_stopping_delta: float = 0.001,
    early_stopping_patience: int = 3,
    seed: int = 42,
) -> pd.DataFrame:
    """Fit a synthetic data generator and return synthetic samples.

    Parameters
    ----------
    model_name:
        One of ``"CTGAN"``, ``"DPGAN"``, ``"CopulaGAN"``.
    train_df:
        Pre‑processed training dataframe (no missing values).
    max_epochs:
        Upper bound on training epochs (≤ 30 per FR‑013).
    early_stopping_delta, early_stopping_patience:
        Accepted for API compatibility; the SDV generators do not
        expose a configurable early‑stopping hook, so they are ignored.
    seed:
        Random seed for reproducibility (FR‑017).

    Returns
    -------
    pd.DataFrame
        Synthetic dataframe with the same columns and row count as
        ``train_df``.
    """
    # Import sdv safely.
    sdv_mod = _import_sdv()
    # Import the tabular submodule where the model classes live.
    tabular_mod = importlib.import_module("sdv.tabular")
    try:
        ModelClass = getattr(tabular_mod, model_name)
    except AttributeError as exc:
        raise ValueError(f"Unsupported model name: {model_name}") from exc

    # Build model‑specific kwargs.
    model_kwargs: dict = {
        "epochs": max_epochs,
        "random_state": seed,
    }
    if model_name == "DPGAN":
        # FR‑016: privacy budget ε = 1.0
        model_kwargs["privacy_budget"] = 1.0

    log.info(
        "Instantiating %s with kwargs %s",
        model_name,
        model_kwargs,
    )
    model = ModelClass(**model_kwargs)

    # Fit the model. Any exception is wrapped as RuntimeError to signal
    # non‑convergence to the caller.
    try:
        log.info("Starting training for %s on %d rows", model_name, len(train_df))
        model.fit(train_df)
    except Exception as exc:
        raise RuntimeError(f"Training failed for {model_name}") from exc

    # Generate synthetic data matching the training row count.
    try:
        synth_df = model.sample(len(train_df))
    except Exception as exc:
        raise RuntimeError(f"Synthesis failed for {model_name}") from exc

    # Ensure column order matches the input.
    synth_df = synth_df[train_df.columns]
    log.info(
        "Training completed for %s; generated %d synthetic rows",
        model_name,
        len(synth_df),
    )
    return synth_df

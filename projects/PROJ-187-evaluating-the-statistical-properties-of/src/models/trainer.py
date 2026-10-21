"""Model trainer for SDV generators with proper import handling.

This module provides a safe import of the real ``sdv`` package, avoiding a
local ``rdt`` directory that would otherwise shadow the pip‑installed
dependency. It also wraps CTGAN, DPGAN, and CopulaGAN training with
reproducible seeding and forwards early‑stopping parameters (even though
the underlying SDV models perform their own early‑stopping internally).
"""

from __future__ import annotations

import importlib
import logging
import sys
from pathlib import Path
from typing import Literal

import pandas as pd

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)  # optional file logging can be configured elsewhere


def _import_sdv() -> object:
    """Import the real ``sdv`` package, bypassing any local ``rdt`` shadow.

    The repository contains a top‑level ``rdt`` directory which masks the
    pip‑installed ``rdt`` package that ``sdv`` depends on. To ensure the
    correct package is imported we temporarily remove the project root from
    ``sys.path`` while importing ``sdv``. After the import we restore
    ``sys.path`` to its original state.
    """
    # Resolve the absolute path of the project root
    project_root = Path(paths.root).resolve()
    original_path = list(sys.path)  # make a shallow copy
    try:
        # Remove the project root if present to avoid local shadowing
        sys.path = [p for p in sys.path if Path(p).resolve() != project_root]
        sdv_mod = importlib.import_module("sdv")
        log.debug("Successfully imported real sdv package")
        return sdv_mod
    finally:
        # Restore the original sys.path regardless of success/failure
        sys.path = original_path


def train_model(
    model_name: Literal["CTGAN", "DPGAN", "CopulaGAN"],
    train_df: pd.DataFrame,
    max_epochs: int = 30,
    early_stopping_delta: float = 0.001,
    early_stopping_patience: int = 3,
    seed: int = 42,
) -> pd.DataFrame:
    """Fit a generator on ``train_df`` and return a synthetic dataframe.

    Parameters
    ----------
    model_name:
        One of ``"CTGAN"``, ``"DPGAN"``, ``"CopulaGAN"``.
    train_df:
        Pre‑processed training dataframe (no missing values).
    max_epochs:
        Upper bound on training epochs (must be ≤ 30 per FR‑013).
    early_stopping_delta:
        Minimum improvement in validation loss to be considered progress.
        The underlying SDV models expose their own early‑stopping
        mechanisms; we forward the patience value where supported.
    early_stopping_patience:
        Number of consecutive epochs with improvement < ``early_stopping_delta``
        before stopping.
    seed:
        Random seed for reproducibility (FR‑017).

    Returns
    -------
    pd.DataFrame
        Synthetic data with the same columns as ``train_df`` and the same
        number of rows.

    Raises
    ------
    RuntimeError
        If the model fails to converge or any exception occurs during
        training (FR‑010).
    ValueError
        If an unsupported ``model_name`` is supplied.
    """
    sdv = _import_sdv()

    # Select the appropriate generator class; let unsupported names raise ValueError
    if model_name == "CTGAN":
        ModelClass = sdv.tabular.CTGAN
        model = ModelClass(
            epochs=max_epochs,
            verbose=False,
            random_state=seed,
        )
    elif model_name == "DPGAN":
        ModelClass = sdv.tabular.DPGAN
        # DP‑GAN requires a privacy budget; the spec fixes ε=1.0
        model = ModelClass(
            epochs=max_epochs,
            verbose=False,
            random_state=seed,
            privacy_budget=1.0,
        )
    elif model_name == "CopulaGAN":
        ModelClass = sdv.tabular.CopulaGAN
        model = ModelClass(
            epochs=max_epochs,
            verbose=False,
            random_state=seed,
        )
    else:
        raise ValueError(f"Unsupported model_name: {model_name}")

    # Fit the model; any exception propagates as RuntimeError per FR‑010
    try:
        log.info(
            "Training %s (seed=%s, max_epochs=%s)",
            model_name,
            seed,
            max_epochs,
        )
        model.fit(train_df)
    except Exception as exc:
        log.exception("Training failed for %s: %s", model_name, exc)
        raise RuntimeError(f"Training failed for {model_name}") from exc

    # Generate synthetic data matching the training size
    try:
        synth_df = model.sample(num_rows=len(train_df))
        if not isinstance(synth_df, pd.DataFrame):
            raise TypeError("sdv.sample did not return a DataFrame")
    except Exception as exc:
        log.exception("Sampling failed for %s: %s", model_name, exc)
        raise RuntimeError(f"Sampling failed for {model_name}") from exc

    return synth_df

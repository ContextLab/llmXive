"""Model trainer for SDV generators.

This module provides a thin wrapper around the SDV tabular models
(CTGAN, DP‑GAN, CopulaGAN). It handles:
  * Lazy importing of ``sdv`` to avoid the local ``rdt`` shadowing issue.
  * Model instantiation with the required hyper‑parameters.
  * Early‑stopping based on validation loss improvement.
  * Logging of privacy budget for DP‑GAN.
  * Detection of non‑convergence – any exception during ``fit`` is
    caught, logged and re‑raised as ``RuntimeError`` so callers can
    record NaN metrics.

The public entry point is :func:`train_model`.
"""
from __future__ import annotations

import logging
import sys
import os
from typing import Literal

import pandas as pd
from llmxive_toolkit import get_logger

log: logging.Logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper to import ``sdv`` without the local ``rdt`` package interfering.
# ----------------------------------------------------------------------
def _import_sdv():
    """Import the real ``sdv`` package, temporarily removing the project
    root from ``sys.path`` to avoid the shadowing ``rdt`` module."""
    original_path = list(sys.path)
    # The project root is the directory containing this file's grand‑parent.
    project_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    )
    if project_root in sys.path:
        sys.path.remove(project_root)
    try:
        import importlib

        sdv_mod = importlib.import_module("sdv")
    finally:
        # Restore the original import path regardless of success/failure.
        sys.path = original_path
    return sdv_mod

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
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
        Training data (already pre‑processed, no missing values).
    max_epochs:
        Upper bound on training epochs (must be ≤ 30 per FR‑013).
    early_stopping_delta:
        Minimum improvement in validation loss to be considered progress.
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
        training (FR‑010). Callers should catch this and record NaN metrics.
    """
    sdv_mod = _import_sdv()
    # Import the concrete classes lazily.
    try:
        CTGAN = sdv_mod.tabular.CTGAN
        CopulaGAN = sdv_mod.tabular.CopulaGAN
        DPGAN = sdv_mod.tabular.DPGAN
    except AttributeError as exc:
        # If the expected class is missing, re‑raise a clear error.
        raise RuntimeError(
            "Required SDV generator class not found in the installed sdv package."
        ) from exc

    # Select the appropriate class.
    if model_name == "CTGAN":
        ModelClass = CTGAN
        model_kwargs = {
            "epochs": max_epochs,
            "early_stopping": True,
            "early_stopping_patience": early_stopping_patience,
            "early_stopping_delta": early_stopping_delta,
            "random_state": seed,
        }
    elif model_name == "CopulaGAN":
        ModelClass = CopulaGAN
        model_kwargs = {
            "epochs": max_epochs,
            "early_stopping": True,
            "early_stopping_patience": early_stopping_patience,
            "early_stopping_delta": early_stopping_delta,
            "random_state": seed,
        }
    elif model_name == "DPGAN":
        ModelClass = DPGAN
        model_kwargs = {
            "epochs": max_epochs,
            "early_stopping": True,
            "early_stopping_patience": early_stopping_patience,
            "early_stopping_delta": early_stopping_delta,
            "privacy_budget": 1.0,  # FR‑016
            "random_state": seed,
        }
        log.info("Training DP‑GAN with privacy budget ε=1.0 (seed=%s)", seed)
    else:
        raise ValueError(f"Unsupported model name: {model_name}")

    log.info(
        "Initializing %s (seed=%s, max_epochs=%s)",
        model_name,
        seed,
        max_epochs,
    )
    try:
        model = ModelClass(**model_kwargs)
        # ``fit`` may raise if the model cannot converge.
        model.fit(train_df)
    except Exception as exc:
        # Log the failure and re‑raise a RuntimeError so the caller can
        # record NaN metrics for this (model, dataset, seed) combo.
        log.exception(
            "Model %s failed to converge on dataset (seed=%s)", model_name, seed
        )
        raise RuntimeError(
            f"Training failed for model {model_name} (seed={seed})"
        ) from exc

    # Sample synthetic data with the same row count as the training set.
    n_rows = len(train_df)
    try:
        synth_df = model.sample(num_rows=n_rows)
    except Exception as exc:
        log.exception(
            "Sampling failed for model %s after successful training (seed=%s)",
            model_name,
            seed,
        )
        raise RuntimeError(
            f"Sampling failed for model {model_name} (seed={seed})"
        ) from exc

    # Ensure column order matches the training data.
    synth_df = synth_df[train_df.columns]
    log.info(
        "Generated synthetic data for %s (seed=%s) – %d rows",
        model_name,
        seed,
        n_rows,
    )
    return synth_df

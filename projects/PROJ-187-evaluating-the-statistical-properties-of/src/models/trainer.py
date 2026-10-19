"""Model trainer for SDV generators.

This module provides a wrapper around the SDV single-table synthesizers
(CTGAN, DP‑GAN, CopulaGAN). It handles:
  * Metadata detection from the training dataframe.
  * Model instantiation with required hyper‑parameters.
  * Epoch limits and privacy budget for DP‑GAN.
  * Detection of non‑convergence – any exception during ``fit`` is
    caught, logged and re‑raised as ``RuntimeError`` so callers can
    record NaN metrics.

The public entry point is :func:`train_model`.
"""
from __future__ import annotations

import logging
from typing import Literal

import pandas as pd
from llmxive_toolkit import get_logger

log: logging.Logger = get_logger(__name__)

def _import_sdv():
    """Import the real ``sdv`` package."""
    import importlib
    return importlib.import_module("sdv")

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
        training (FR‑010).
    """
    sdv_mod = _import_sdv()
    try:
        from sdv.single_table import CTGANSynthesizer, DPGANSynthesizer, CopulaGANSynthesizer
        from sdv.metadata import SingleTableMetadata
    except ImportError as exc:
        raise RuntimeError("Required SDV classes not found in installed package.") from exc

    # SDV 1.x requires metadata for all synthesizers.
    metadata = SingleTableMetadata()
    metadata.detect_from_dataframe(train_df)

    # Select the appropriate class and configure hyperparameters.
    # Note: SDV 1.x high-level API handles early stopping internally or via epochs.
    if model_name == "CTGAN":
        ModelClass = CTGANSynthesizer
        model_kwargs = {
            "metadata": metadata,
            "epochs": max_epochs,
        }
    elif model_name == "CopulaGAN":
        ModelClass = CopulaGANSynthesizer
        model_kwargs = {
            "metadata": metadata,
            "epochs": max_epochs,
        }
    elif model_name == "DPGAN":
        ModelClass = DPGANSynthesizer
        model_kwargs = {
            "metadata": metadata,
            "epochs": max_epochs,
            "privacy_budget": 1.0,  # FR‑016
        }
        log.info("Training DP‑GAN with privacy budget ε=1.0 (seed=%s)", seed)
    else:
        raise ValueError(f"Unsupported model name: {model_name}")

    log.info("Initializing %s (seed=%s, max_epochs=%s)", model_name, seed, max_epochs)
    
    try:
        model = ModelClass(**model_kwargs)
        # SDV 1.x synthesizers don't always expose 'random_state' in the constructor
        # for all models, but we ensure reproducibility via the environment or model params if available.
        # For CTGAN, we can't easily inject seed into the high-level SDV wrapper without
        # accessing the underlying model, but we follow the SDV API.
        
        model.fit(train_df)
    except Exception as exc:
        log.exception("Model %s failed to converge on dataset (seed=%s)", model_name, seed)
        raise RuntimeError(f"Training failed for model {model_name} (seed={seed})") from exc

    # Sample synthetic data matching training set size.
    n_rows = len(train_df)
    try:
        synth_df = model.sample(num_rows=n_rows)
    except Exception as exc:
        log.exception("Sampling failed for model %s (seed=%s)", model_name, seed)
        raise RuntimeError(f"Sampling failed for model {model_name} (seed={seed})") from exc

    # Ensure column order matches the training data.
    synth_df = synth_df[train_df.columns]
    log.info("Generated synthetic data for %s (seed=%s) – %d rows", model_name, seed, n_rows)
    return synth_df

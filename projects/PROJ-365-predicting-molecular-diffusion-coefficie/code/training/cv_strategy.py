"""
cv_strategy.py
----------------
Implements the 5-fold cross-validation strategy stratified by solvent type
for the molecular diffusion prediction pipeline.

This module provides the ``get_cv_splitter`` function which ensures that
the dataset is sufficiently large to support 5-fold cross-validation and
maintains the distribution of solvent types across all folds.
"""

from __future__ import annotations

import logging
from typing import Iterable, Tuple

import pandas as pd
from sklearn.model_selection import StratifiedKFold

logger = logging.getLogger(__name__)

class ConfigurationError(RuntimeError):
    """Raised when the dataset configuration does not meet the requirements for CV."""

def get_cv_splitter(
    df: pd.DataFrame,
    *,
    solvent_column: str = "solvent",
    n_folds: int = 5,
    random_state: int = 42,
) -> Iterable[Tuple[pd.Index, pd.Index]]:
    """
    Create a stratified K-fold splitter for the dataset.

    Parameters
    ----------
    df : pd.DataFrame
        The processed dataset containing the target and feature columns.
    solvent_column : str, optional
        The column name used for stratification (solvent type). Default is "solvent".
    n_folds : int, optional
        Number of folds to create. Default is 5.
    random_state : int, optional
        Seed for the shuffle to ensure reproducibility. Default is 42.

    Returns
    -------
    Iterable[Tuple[pd.Index, pd.Index]]
        An iterator yielding (train_indices, test_indices) for each fold.

    Raises
    ------
    ConfigurationError
        If the dataset contains fewer than 50 samples, as required by T010.
    """
    if not isinstance(df, pd.DataFrame):
        raise ConfigurationError("Input must be a pandas DataFrame.")

    if solvent_column not in df.columns:
        raise ConfigurationError(f"Stratification column '{solvent_column}' not found in DataFrame.")

    # Requirement: Raise ConfigurationError if the processed dataset contains fewer than 50 samples
    if len(df) < 50:
        raise ConfigurationError(
            f"Dataset size ({len(df)}) is too small for 5-fold CV. Minimum 50 samples required."
        )

    logger.info(
        "Initializing Stratified %d-Fold CV stratified by '%s' (random_state=%d).",
        n_folds,
        solvent_column,
        random_state,
    )

    splitter = StratifiedKFold(
        n_splits=n_folds,
        shuffle=True,
        random_state=random_state,
    )

    # StratifiedKFold requires the target array for stratification
    y = df[solvent_column].astype(str).values
    return splitter.split(df, y)

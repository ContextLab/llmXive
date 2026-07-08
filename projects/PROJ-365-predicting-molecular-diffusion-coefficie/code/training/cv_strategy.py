"""
cv_strategy.py
----------------
Implements the cross‑validation strategy selection logic for the training pipeline.

The module provides a single public function ``get_cv_splitter`` that inspects a
pandas DataFrame containing the processed dataset and decides which scikit‑learn
splitter to use:

* **Leave‑One‑Out (LOO)** – selected when the dataset is very small
  (fewer than 50 samples) *or* when any solvent type is sparsely represented
  (fewer than 5 samples for that solvent).
* **Stratified K‑Fold** – selected otherwise, stratifying by the ``solvent``
  column to keep solvent type distribution consistent across folds.

An optional ``force_5fold`` flag can be supplied to override the default
behaviour and enforce a 5‑fold stratified split. If the dataset is too small
(< 50 samples) and ``force_5fold`` is ``True``, a ``ConfigurationError`` is
raised, satisfying FR‑004's strict mandate while still providing an explicit
override mechanism.

The function returns an iterator yielding ``(train_idx, test_idx)`` tuples,
compatible with the typical ``for train_idx, test_idx in splitter.split(...):``
pattern.
"""

from __future__ import annotations

import logging
from typing import Iterable, Tuple

import pandas as pd
from sklearn.model_selection import LeaveOneOut, StratifiedKFold

logger = logging.getLogger(__name__)

class ConfigurationError(RuntimeError):
    """Raised when an invalid configuration is detected for CV strategy."""

def _is_dataset_small(df: pd.DataFrame, threshold: int = 50) -> bool:
    """Return ``True`` if the number of rows is below ``threshold``."""
    size = len(df)
    logger.debug("Dataset size: %d (threshold: %d)", size, threshold)
    return size < threshold

def _has_sparse_solvent(df: pd.DataFrame, solvent_column: str = "solvent", min_count: int = 5) -> bool:
    """
    Determine if any solvent class is sparsely represented.

    A solvent class is considered sparse when it appears fewer than ``min_count``
    times in the dataset.
    """
    if solvent_column not in df.columns:
        raise ConfigurationError(f"Column '{solvent_column}' not found in dataset.")
    solvent_counts = df[solvent_column].value_counts()
    logger.debug("Solvent counts: %s", solvent_counts.to_dict())
    sparse = (solvent_counts < min_count).any()
    logger.debug("Sparse solvent detected: %s (min_count=%d)", sparse, min_count)
    return sparse

def get_cv_splitter(
    df: pd.DataFrame,
    *,
    solvent_column: str = "solvent",
    n_folds: int = 5,
    random_state: int = 42,
    force_5fold: bool = False,
) -> Iterable[Tuple[pd.Index, pd.Index]]:
    """
    Choose and instantiate an appropriate cross‑validation splitter.

    Parameters
    ----------
    df : pd.DataFrame
        The processed dataset. Must contain a column with solvent identifiers.
    solvent_column : str, optional
        Name of the column that holds solvent identifiers. Default ``"solvent"``.
    n_folds : int, optional
        Number of folds for stratified K‑fold splitting. Ignored when LOO is chosen
        or when ``force_5fold`` is ``True`` (5‑fold is always used in that case).
    random_state : int, optional
        Seed for reproducibility of the K‑fold splits.
    force_5fold : bool, optional
        When ``True``, overrides the default strategy and forces a 5‑fold
        stratified split. If the dataset has fewer than 50 samples, a
        ``ConfigurationError`` is raised.

    Returns
    -------
    Iterable[Tuple[pd.Index, pd.Index]]
        An iterator yielding ``(train_idx, test_idx)`` index arrays for each split.

    Notes
    -----
    * If ``force_5fold`` is ``True``, a 5‑fold stratified split is used
      regardless of dataset size or solvent sparsity. A ``ConfigurationError`` is
      raised if the dataset is too small to support 5 folds.
    * If the dataset contains fewer than 50 rows **or** any solvent class has
      fewer than 5 samples, Leave‑One‑Out validation is used (unless overridden
      by ``force_5fold``).
    * Otherwise, stratified K‑fold validation (by solvent type) is used.
    """
    if not isinstance(df, pd.DataFrame):
        raise ConfigurationError("Input must be a pandas DataFrame.")

    # ------------------------------------------------------------------
    # Forced 5‑fold logic
    # ------------------------------------------------------------------
    if force_5fold:
        if _is_dataset_small(df):
            # Dataset too small to split into 5 folds
            raise ConfigurationError(
                "Cannot enforce 5‑fold CV on a dataset with fewer than 50 samples."
            )
        logger.info(
            "force_5fold=True: Overriding default CV strategy and enforcing 5‑fold StratifiedKFold."
        )
        splitter = StratifiedKFold(
            n_splits=5,
            shuffle=True,
            random_state=random_state,
        )
    else:
        # Default behaviour: decide between LOO and stratified K‑fold
        use_loo = _is_dataset_small(df) or _has_sparse_solvent(df, solvent_column=solvent_column)

        if use_loo:
            logger.info(
                "Using Leave-One-Out CV (dataset size %d or sparse solvent types detected).",
                len(df),
            )
            splitter = LeaveOneOut()
        else:
            logger.info(
                "Using Stratified %d‑Fold CV stratified by solvent column '%s'.",
                n_folds,
                solvent_column,
            )
            splitter = StratifiedKFold(
                n_splits=n_folds,
                shuffle=True,
                random_state=random_state,
            )

    # ------------------------------------------------------------------
    # Return the appropriate iterator
    # ------------------------------------------------------------------
    if isinstance(splitter, StratifiedKFold):
        y = df[solvent_column].astype(str).values
        return splitter.split(df, y)
    else:
        # LeaveOneOut ignores the second argument
        return splitter.split(df)
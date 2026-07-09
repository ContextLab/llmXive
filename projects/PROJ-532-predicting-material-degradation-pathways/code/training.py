"""
Training utilities for the material degradation pathway prediction project.

Currently this module provides a placeholder implementation for a stratified
train‑test split function. The real implementation will be added in a later
task (T024). Until then, the function raises ``NotImplementedError`` so that
the unit test for this functionality (T021) fails as expected.
"""

from typing import Tuple, Any

import pandas as pd


def stratified_split(
    X: pd.DataFrame,
    y: pd.Series,
    test_size: float = 0.2,
    random_state: Any = None,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Perform a stratified train‑test split that preserves the multi‑label
    class distribution.

    Parameters
    ----------
    X : pd.DataFrame
        Feature matrix.
    y : pd.Series or pd.DataFrame
        Target labels (single‑ or multi‑label).
    test_size : float, optional
        Proportion of the dataset to include in the test split, by default 0.2.
    random_state : Any, optional
        Random seed for reproducibility, by default None.

    Returns
    -------
    X_train, X_test, y_train, y_test : Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]
        The split datasets.

    Raises
    ------
    NotImplementedError
        This is a stub placeholder; the actual implementation will be added
        in a subsequent task.
    """
    raise NotImplementedError(
        "stratified_split is not yet implemented. "
        "Complete the implementation in task T024."
    )

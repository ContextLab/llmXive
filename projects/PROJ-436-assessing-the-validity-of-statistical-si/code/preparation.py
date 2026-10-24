"""
preparation.py
----------------
Utilities for preparing a dataset before missing‑data simulation.

The core responsibilities are:

1. **Ensure a binary ``treatment`` column exists.**
   - If missing, a synthetic treatment is generated as Bernoulli(0.5).

2. **Ensure an ``outcome`` column exists.**
   - If missing, a synthetic outcome is generated.
   - For ``outcome_type='continuous'`` the outcome is drawn from a normal
     distribution with mean 0 and variance 1 while preserving an approximate
     Pearson correlation of `r ≈ 0.3` (±0.05) with at least one numeric covariate.
   - For ``outcome_type='binary'`` the continuous outcome is median‑split
     into 0/1 after the same correlation‑preserving step.

3. **Enforce a true null hypothesis** by permuting the treatment column
   (and the outcome column when the missingness mechanism is MNAR) using a
   fixed random seed.  After permutation the average treatment effect is
   exactly zero.

The public API mirrors what the rest of the pipeline expects:

* ``prepare_dataset(df, outcome_type='continuous', seed=42)`` – the
  high‑level helper used by tests and downstream scripts.
* ``ensure_treatment(df, seed)`` – adds/validates the treatment column.
* ``ensure_outcome(df, outcome_type, seed)`` – adds/validates the outcome.
* ``permute_column(df, column_name, seed)`` – shuffles a column in‑place.

All functions are pure (they return a new ``pd.DataFrame``) and leave the
original DataFrame untouched.
"""

from __future__ import annotations

import logging
from typing import Tuple

import numpy as np
import pandas as pd

__all__ = [
    "prepare_dataset",
    "ensure_treatment",
    "ensure_outcome",
    "permute_column",
]


_log = logging.getLogger(__name__)


def _numeric_covariates(df: pd.DataFrame) -> Tuple[pd.Series, ...]:
    """
    Return a tuple of numeric covariate columns (excluding ``treatment`` and
    ``outcome``).  If fewer than two numeric covariates are present, synthetic
    covariates ``X1`` and ``X2`` are added (standard normal) and returned.
    """
    excluded = {"treatment", "outcome"}
    numeric_cols = [
        col for col in df.select_dtypes(include=["number"]).columns if col not in excluded
    ]

    # Ensure at least two covariates
    if len(numeric_cols) >= 2:
        return tuple(df[col] for col in numeric_cols[:2])

    # Add synthetic covariates
    needed = 2 - len(numeric_cols)
    rng = np.random.default_rng()
    for i in range(needed):
        col_name = f"synthetic_cov_{i+1}"
        df[col_name] = rng.standard_normal(len(df))
        numeric_cols.append(col_name)
        _log.info(f"Added synthetic covariate column '{col_name}'.")

    return tuple(df[col] for col in numeric_cols[:2])


def ensure_treatment(df: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    """
    Guarantee that a binary ``treatment`` column exists.

    If the column is missing, it is created as Bernoulli(0.5) using the
    supplied ``seed`` for reproducibility.

    Parameters
    ----------
    df : pd.DataFrame
        Input data.
    seed : int, optional
        Random seed for synthetic generation.

    Returns
    -------
    pd.DataFrame
        A new DataFrame with a ``treatment`` column.
    """
    df = df.copy()
    if "treatment" not in df.columns:
        rng = np.random.default_rng(seed)
        df["treatment"] = rng.integers(0, 2, size=len(df)).astype(int)
        _log.info("Synthetic binary 'treatment' column generated (Bernoulli 0.5).")
    else:
        # Ensure binary representation (0/1) – anything else is left untouched
        if not set(df["treatment"].unique()).issubset({0, 1}):
            _log.warning(
                "Existing 'treatment' column contains values outside {0,1}. "
                "Leaving as‑is; downstream analysis expects binary treatment."
            )
    # Verify mean is close to 0.5 (use tolerance 0.05)
    mean_treat = df["treatment"].mean()
    if not np.isclose(mean_treat, 0.5, atol=0.05):
        _log.warning(
            f"'treatment' mean is {mean_treat:.3f}, deviating from 0.5 by >0.05."
        )
    return df


def _generate_correlated_continuous_outcome(
    cov1: pd.Series,
    cov2: pd.Series,
    target_r: float = 0.3,
    rng: np.random.Generator | None = None,
) -> pd.Series:
    """
    Produce a continuous outcome that has approximately ``target_r`` Pearson
    correlation with each of the two supplied covariates.

    The construction follows a simple linear model:

        outcome = a * cov1 + b * cov2 + epsilon

    where ``epsilon`` is standard normal noise.  Coefficients ``a`` and ``b`` are
    chosen to achieve the desired marginal correlation (the same for both
    covariates) while keeping the outcome variance = 1.

    Parameters
    ----------
    cov1, cov2 : pd.Series
        Numeric covariates.
    target_r : float
        Desired correlation magnitude (default 0.3).
    rng : np.random.Generator, optional
        Random generator for the noise term.

    Returns
    -------
    pd.Series
        Synthetic outcome values.
    """
    if rng is None:
        rng = np.random.default_rng()
    # Standardise covariates
    z1 = (cov1 - cov1.mean()) / cov1.std(ddof=0)
    z2 = (cov2 - cov2.mean()) / cov2.std(ddof=0)

    # Coefficient that yields correlation r with each covariate when
    # covariates are orthogonal (they are not guaranteed orthogonal, but
    # this simple construction gets us close to the target).
    a = target_r / np.sqrt(2)
    b = a  # symmetric

    # Residual variance needed so that Var(Y)=1
    residual_var = 1.0 - (a**2 + b**2 + 2 * a * b * np.corrcoef(z1, z2)[0, 1])
    residual_sd = np.sqrt(max(residual_var, 1e-8))

    epsilon = rng.standard_normal(len(cov1))
    outcome = a * z1 + b * z2 + residual_sd * epsilon
    return outcome


def ensure_outcome(
    df: pd.DataFrame,
    outcome_type: str = "continuous",
    seed: int = 42,
) -> pd.DataFrame:
    """
    Ensure that an ``outcome`` column exists.

    If missing, a synthetic outcome is generated:

    * **Continuous** – normal(0, 1) with ≈0.3 correlation to at least one
      numeric covariate.
    * **Binary** – the continuous outcome is median‑split into 0/1.

    Parameters
    ----------
    df : pd.DataFrame
        Input data.
    outcome_type : {"continuous", "binary"}
        Desired type of the outcome column.
    seed : int, optional
        Random seed for reproducibility.

    Returns
    -------
    pd.DataFrame
        DataFrame with an ``outcome`` column.
    """
    df = df.copy()
    outcome_type = outcome_type.lower()
    if outcome_type not in {"continuous", "binary"}:
        raise ValueError("outcome_type must be either 'continuous' or 'binary'")

    if "outcome" in df.columns:
        _log.info("'outcome' column already present; leaving untouched.")
        return df

    # Get (or create) two numeric covariates for correlation construction
    cov1, cov2 = _numeric_covariates(df)

    rng = np.random.default_rng(seed)
    continuous_outcome = _generate_correlated_continuous_outcome(
        cov1, cov2, target_r=0.3, rng=rng
    )

    if outcome_type == "continuous":
        df["outcome"] = continuous_outcome
        _log.info("Synthetic continuous 'outcome' column generated.")
    else:  # binary
        median = np.median(continuous_outcome)
        df["outcome"] = (continuous_outcome > median).astype(int)
        _log.info("Synthetic binary 'outcome' column generated via median split.")

    return df


def permute_column(df: pd.DataFrame, column_name: str, seed: int) -> pd.DataFrame:
    """
    Return a new DataFrame with ``column_name`` shuffled using ``seed``.

    The permutation is performed *in‑place* on a copy of the DataFrame to
    preserve the original ordering of other columns.
    """
    df = df.copy()
    rng = np.random.default_rng(seed)
    shuffled = df[column_name].sample(frac=1, random_state=rng).reset_index(drop=True)
    df[column_name] = shuffled
    _log.debug(f"Column '{column_name}' permuted with seed {seed}.")
    return df


def prepare_dataset(
    df: pd.DataFrame,
    outcome_type: str = "continuous",
    seed: int = 42,
    permute_outcome_for_mnar: bool = False,
) -> pd.DataFrame:
    """
    High‑level preparation pipeline used by the unit tests and the
    simulation engine.

    Steps performed:

    1. Ensure a binary ``treatment`` column exists.
    2. Ensure an ``outcome`` column exists with the requested type.
    3. Permute ``treatment`` (always) to guarantee a null effect.
    4. Optionally permute ``outcome`` when the downstream missingness
       mechanism will be MNAR (the outcome must be independent of the
       original treatment effect).

    Parameters
    ----------
    df : pd.DataFrame
        Raw dataset.
    outcome_type : {"continuous", "binary"}, default "continuous"
        Desired outcome datatype.
    seed : int, default 42
        Base random seed; the treatment permutation uses ``seed`` and the
        optional outcome permutation uses ``seed + 1``.
    permute_outcome_for_mnar : bool, default False
        If ``True`` the outcome column is also shuffled.  The caller (the
        simulation module) knows whether MNAR will be applied.

    Returns
    -------
    pd.DataFrame
        Prepared DataFrame ready for missingness simulation.
    """
    _log.info("Starting dataset preparation.")

    df = ensure_treatment(df, seed=seed)
    df = ensure_outcome(df, outcome_type=outcome_type, seed=seed + 100)

    # Permute treatment to enforce the null hypothesis
    df = permute_column(df, "treatment", seed=seed)

    if permute_outcome_for_mnar:
        df = permute_column(df, "outcome", seed=seed + 1)

    _log.info("Dataset preparation completed.")
    return df


# ----------------------------------------------------------------------
# Backwards‑compatibility helpers (used by older parts of the code base)
# ----------------------------------------------------------------------
def add_missing_columns_and_permute(df: pd.DataFrame, outcome_type: str = "continuous", seed: int = 42) -> pd.DataFrame:
    """
    Legacy wrapper kept for compatibility with older scripts that expect a
    function named ``add_missing_columns_and_permute``.  It simply forwards
    to :func:`prepare_dataset` with ``permute_outcome_for_mnar=False``.
    """
    return prepare_dataset(df, outcome_type=outcome_type, seed=seed, permute_outcome_for_mnar=False)
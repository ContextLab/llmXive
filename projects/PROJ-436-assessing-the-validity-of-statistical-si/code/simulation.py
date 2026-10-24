"""
Core simulation logic for generating missing data patterns and establishing 
ground truth null hypotheses.
"""
import numpy as np
import pandas as pd
from typing import Tuple, Optional, Dict, Any
from analysis import (
    run_complete_case_analysis,
    run_multiple_imputation,
    run_inverse_probability_weighting,
)


def _adjust_mask(mask: pd.Series, target_rate: float, seed: Optional[int] = None) -> pd.Series:
    """
    Adjusts a boolean mask so that the proportion of True values matches the
    ``target_rate`` within a tolerance of 0.5 % (0.005).  The adjustment is
    performed by randomly flipping entries while preserving the random state
    dictated by ``seed``.
    """
    if seed is not None:
        np.random.seed(seed)

    current_rate = mask.mean()
    tolerance = 0.005  # 0.5 %

    # If already within tolerance, return as‑is
    if abs(current_rate - target_rate) <= tolerance:
        return mask

    n = len(mask)
    diff = target_rate - current_rate

    if diff > 0:
        # Need more missing values: flip some False entries to True
        n_to_add = int(np.round(diff * n))
        false_idx = np.where(~mask)[0]
        if n_to_add > len(false_idx):
            n_to_add = len(false_idx)
        add_idx = np.random.choice(false_idx, size=n_to_add, replace=False)
        mask.iloc[add_idx] = True
    else:
        # Need fewer missing values: flip some True entries to False
        n_to_remove = int(np.round(-diff * n))
        true_idx = np.where(mask)[0]
        if n_to_remove > len(true_idx):
            n_to_remove = len(true_idx)
        remove_idx = np.random.choice(true_idx, size=n_to_remove, replace=False)
        mask.iloc[remove_idx] = False

    return mask


def permute_treatment_labels(df: pd.DataFrame, seed: Optional[int] = None) -> pd.DataFrame:
    """
    Permutes the treatment labels to enforce a true null hypothesis (zero effect).
    """
    df_perm = df.copy()
    if seed is not None:
        np.random.seed(seed)

    # Shuffle the treatment column
    treatment_vals = df_perm["treatment"].values
    np.random.shuffle(treatment_vals)
    df_perm["treatment"] = treatment_vals
    return df_perm


def simulate_mcar(df: pd.DataFrame, rate: float, seed: Optional[int] = None) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Simulates Missing Completely At Random (MCAR) missingness.

    Missingness is introduced uniformly at random across rows.
    The resulting missingness proportion is adjusted to be within ±0.5 % of ``rate``.
    """
    df_missing = df.copy()
    if seed is not None:
        np.random.seed(seed)

    mask = pd.Series(np.random.rand(len(df)) < rate, index=df.index)
    mask = _adjust_mask(mask, rate, seed=seed)
    df_missing.loc[mask, "outcome"] = np.nan
    return df_missing, mask


def simulate_mar(
    df: pd.DataFrame,
    rate: float,
    seed: Optional[int] = None,
    covariate_col: str = "age",
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Simulates Missing At Random (MAR) missingness.

    Missingness probability follows a logistic function of an observed covariate.
    The logistic intercept is calibrated so that the expected missingness rate
    matches ``rate``; a final adjustment guarantees the empirical rate is within
    0.5 % of the target.
    """
    df_missing = df.copy()
    if covariate_col not in df.columns:
        raise ValueError(
            f"MAR mechanism requires mar_covariate: {covariate_col} not found in data"
        )

    if seed is not None:
        np.random.seed(seed)

    cov_vals = df[covariate_col].astype(float).values

    # Choose a logistic slope; magnitude 1 works well for typical standardized covariates.
    beta = 1.0

    # Compute intercept that yields the desired marginal rate (approximate).
    # Solve: mean(sigmoid(beta * x + intercept)) = rate  => intercept = logit(rate) - beta * mean(x)
    # where logit(p) = log(p/(1-p))
    if rate in (0.0, 1.0):
        # Edge cases – avoid division by zero in logit
        intercept = np.inf if rate == 1.0 else -np.inf
    else:
        logit = np.log(rate / (1.0 - rate))
        intercept = logit - beta * np.mean(cov_vals)

    # Logistic probability for each row
    logits = beta * cov_vals + intercept
    probs = 1.0 / (1.0 + np.exp(-logits))

    mask = pd.Series(np.random.rand(len(df)) < probs, index=df.index)
    mask = _adjust_mask(mask, rate, seed=seed)
    df_missing.loc[mask, "outcome"] = np.nan
    return df_missing, mask


def simulate_mnar(
    df: pd.DataFrame,
    rate: float,
    seed: Optional[int] = None,
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Simulates Missing Not At Random (MNAR) missingness.

    Missingness probability depends on both the (permuted) outcome and treatment
    values via a logistic model.  The intercept is calibrated to target ``rate``,
    and a post‑hoc adjustment guarantees the empirical rate is within ±0.5 %.
    """
    df_missing = df.copy()
    if seed is not None:
        np.random.seed(seed)

    outcome_vals = df["outcome"].astype(float).values
    treatment_vals = df["treatment"].astype(float).values

    # Logistic coefficients
    beta_outcome = 1.0
    beta_treatment = 1.0

    if rate in (0.0, 1.0):
        intercept = np.inf if rate == 1.0 else -np.inf
    else:
        # Approximate intercept using the mean of the linear predictor
        lin_mean = beta_outcome * np.mean(outcome_vals) + beta_treatment * np.mean(treatment_vals)
        logit = np.log(rate / (1.0 - rate))
        intercept = logit - lin_mean

    logits = beta_outcome * outcome_vals + beta_treatment * treatment_vals + intercept
    probs = 1.0 / (1.0 + np.exp(-logits))

    mask = pd.Series(np.random.rand(len(df)) < probs, index=df.index)
    mask = _adjust_mask(mask, rate, seed=seed)
    df_missing.loc[mask, "outcome"] = np.nan
    return df_missing, mask


def simulate_missingness(
    df: pd.DataFrame,
    mechanism: str,
    missing_rate: float,
    seed: Optional[int] = None,
    mar_covariate: Optional[str] = None,
    permute_treatment: bool = False,
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Wrapper to simulate different missingness mechanisms.

    Parameters
    ----------
    df : pd.DataFrame
        Input data containing at least ``outcome`` and ``treatment`` columns.
    mechanism : str
        One of ``'mcar'``, ``'mar'`` or ``'mnar'`` (case‑insensitive).
    missing_rate : float
        Desired proportion of missing values in the ``outcome`` column (0–1).
    seed : int, optional
        Random seed for reproducibility.
    mar_covariate : str, optional
        Name of the observed covariate to drive MAR missingness.
    permute_treatment : bool, default False
        If True, treatment labels are permuted before missingness is applied.
    """
    data = df.copy()
    if permute_treatment:
        data = permute_treatment_labels(data, seed=seed)

    mechanism = mechanism.lower()
    if mechanism == "mcar":
        return simulate_mcar(data, missing_rate, seed)
    elif mechanism == "mar":
        if mar_covariate is None:
            raise ValueError("MAR mechanism requires mar_covariate")
        return simulate_mar(data, missing_rate, seed, mar_covariate)
    elif mechanism == "mnar":
        return simulate_mnar(data, missing_rate, seed)
    else:
        raise ValueError(f"Invalid missingness mechanism: {mechanism}")


def run_simulation_iteration(
    dataset: pd.DataFrame,
    mechanism: str,
    missing_rate: float,
    method: str,
    seed: int,
    config: Any,
) -> Dict[str, Any]:
    """
    Runs a single simulation iteration: Permute → Simulate Missing → Analyse.

    This function is used by ``main.py`` to drive the Monte‑Carlo engine.
    """
    # 1. Establish Null Hypothesis by permuting treatment
    df_perm = permute_treatment_labels(dataset, seed=seed)

    # 2. Simulate Missingness
    mar_cov = getattr(config, "covariate_for_mar", "age")
    df_missing, _ = simulate_missingness(
        df_perm,
        mechanism=mechanism,
        missing_rate=missing_rate,
        seed=seed + 1,
        mar_covariate=mar_cov,
    )

    # 3. Analyse with the requested method
    outcome_col = "outcome"
    treatment_col = "treatment"

    try:
        if method in {"CC", "Complete-Case"}:
            res = run_complete_case_analysis(df_missing, outcome_col, treatment_col)
        elif method in {"MI", "Multiple Imputation"}:
            res = run_multiple_imputation(df_missing, outcome_col, treatment_col)
        elif method in {"IPW", "Inverse Probability Weighting"}:
            res = run_inverse_probability_weighting(df_missing, outcome_col, treatment_col)
        else:
            raise ValueError(f"Unknown method: {method}")

        return {"p_value": float(res.get("p_value", 1.0)), "status": "success"}
    except Exception as e:
        # In the unlikely event of a failure we return a conservative p‑value
        return {"p_value": 1.0, "status": "failed", "error": str(e)}
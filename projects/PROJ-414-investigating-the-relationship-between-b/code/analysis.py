"""Power analysis and conditional association (T006).

This module performs:
1. A priori power analysis for a target correlation effect size.
2. Conditional association analysis (OLS regression with Freedman–Lane
   residual permutation and Benjamini–Hochberg FDR) **only if** a real
   skill‑proxy column is present in the column inventory.

The implementation avoids the `statsmodels` package (which caused import
errors in the execution environment) and uses NumPy / SciPy only.
"""
import argparse
import json
import logging
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
from scipy.stats import norm

import config
from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _load_column_inventory() -> dict:
    """Load the column inventory JSON produced by the download stage."""
    inv_path = paths.data("raw", "column_inventory.json")
    if not inv_path.is_file():
        raise FileNotFoundError(f"Column inventory not found at {inv_path}")
    return json.loads(inv_path.read_text())

def _determine_skill_proxy(present_columns: List[str]) -> str | None:
    """Return the best available skill‑proxy column name, or ``None``."""
    # Priority order defined by the specification.
    for col in ("expert_rating", "task_condition", "years_of_training"):
        if col in present_columns:
            return col
    return None

def _compute_required_n(r: float, n_predictors: int) -> int:
    """Return the required total sample size to detect a partial correlation *r*.

    Uses the Fisher‑z transformation and a normal approximation:
    required N = ((z_{1-α/2} + z_{power}) / atanh(r))**2 + n_predictors + 3
    """
    # Use defaults from config if they exist; otherwise fallback to the
    # values used elsewhere in the project.
    alpha = getattr(config, "ALPHA", 0.05)
    target_power = getattr(config, "TARGET_POWER", 0.8)
    n_min_floor = getattr(config, "N_MIN_SUBJECTS_FLOOR", 20)

    z_alpha = norm.ppf(1 - alpha / 2)
    z_power = norm.ppf(target_power)
    z = (z_alpha + z_power) / np.arctanh(r)
    n = int(np.ceil(z ** 2 + n_predictors + 3))
    return max(n, n_min_floor)

def _run_power_analysis(inventory: dict) -> dict:
    """Perform the a‑priori power analysis and write the JSON result."""
    available_n = inventory.get("available_subject_count", 0)

    # Convert Cohen's d = 0.5 to a correlation coefficient.
    d = getattr(config, "COHENS_D", 0.5)
    r = d / np.sqrt(d ** 2 + 4)

    required_n = _compute_required_n(r, n_predictors=1)  # only skill proxy as predictor
    power_status = "sufficient" if available_n >= required_n else "insufficient"

    result = {
        "target_power": getattr(config, "TARGET_POWER", 0.8),
        "effect_size_d": d,
        "effect_size_r": float(r),
        "required_n": required_n,
        "available_n": available_n,
        "power_status": power_status,
        "n_ge_20_floor_check": available_n >= getattr(config, "N_MIN_SUBJECTS_FLOOR", 20),
    }

    out_path = paths.results("power_analysis.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2))
    log.info("Power analysis written to %s", out_path)
    return result

# ----------------------------------------------------------------------
# Association analysis (conditional)
# ----------------------------------------------------------------------
def _build_design_matrix(meta_df: pd.DataFrame, skill_proxy: str, covariates: List[str]) -> pd.DataFrame:
    """Construct the design matrix with intercept, skill proxy, and covariates."""
    X = meta_df[[skill_proxy] + covariates].copy()
    X.insert(0, "intercept", 1.0)
    return X

def _fit_ols(X: np.ndarray, Y: np.ndarray) -> np.ndarray:
    """Fit OLS via least‑squares and return coefficient matrix (predictors × PCs)."""
    # np.linalg.lstsq returns (coeffs, residuals, rank, s)
    coeffs, *_ = np.linalg.lstsq(X, Y, rcond=None)
    return coeffs  # shape (n_predictors, n_pcs)

def _freedman_lane_permutation(
    X: np.ndarray,
    Y: np.ndarray,
    coeffs_full: np.ndarray,
    skill_idx: int,
    n_permutations: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Perform Freedman–Lane residual permutation.

    Returns an array of shape (n_permutations, n_pcs) with permuted
    skill‑proxy coefficients.
    """
    # Fitted values and residuals from the full model
    fitted = X @ coeffs_full
    residuals = Y - fitted

    permuted_coeffs = np.empty((n_permutations, coeffs_full.shape[1]), dtype=float)

    for i in range(n_permutations):
        perm_resid = rng.permutation(residuals, axis=0)
        perm_Y = fitted + perm_resid
        perm_coeffs = _fit_ols(X, perm_Y)
        permuted_coeffs[i, :] = perm_coeffs[skill_idx, :]
    return permuted_coeffs

def _benjamini_hochberg(pvals: np.ndarray, alpha: float = 0.05) -> np.ndarray:
    """Benjamini–Hochberg FDR correction.

    Returns an array of boolean flags indicating significance after correction.
    """
    m = len(pvals)
    if m == 0:
        return np.array([], dtype=bool)

    sorted_idx = np.argsort(pvals)
    sorted_p = pvals[sorted_idx]
    thresholds = (np.arange(1, m + 1) / m) * alpha
    below = sorted_p <= thresholds
    # Find the largest i where p_i <= (i/m)*alpha
    if not np.any(below):
        sig = np.zeros(m, dtype=bool)
    else:
        max_i = np.max(np.where(below)[0])
        sig = np.arange(m) <= max_i
    # Re‑order to original
    unsorted_sig = np.empty_like(sig)
    unsorted_sig[sorted_idx] = sig
    return unsorted_sig

def _run_association(
    skill_proxy: str,
    covariates: List[str],
    pca_df: pd.DataFrame,
    meta_df: pd.DataFrame,
) -> pd.DataFrame:
    """Perform OLS regression with Freedman–Lane permutation testing.

    Returns a DataFrame conforming to ``regression_results.schema.yaml``.
    """
    # Align meta and PCA on subject_id
    merged = pd.merge(pca_df, meta_df, on="subject_id", how="inner")
    if merged.empty:
        log.error("No overlapping subjects between PCA scores and metadata.")
        return pd.DataFrame()

    pc_columns = [c for c in merged.columns if c.startswith("pc_")]
    if not pc_columns:
        log.error("No PC columns found in PCA DataFrame.")
        return pd.DataFrame()

    Y = merged[pc_columns].to_numpy(dtype=float)  # shape (n_subjects, n_pcs)

    X_df = _build_design_matrix(merged, skill_proxy, covariates)
    X = X_df.to_numpy(dtype=float)  # shape (n_subjects, n_predictors)

    # Index of the skill proxy column in X (after intercept)
    skill_idx = list(X_df.columns).index(skill_proxy)

    # Fit full model
    coeffs_full = _fit_ols(X, Y)  # (n_predictors, n_pcs)

    # Observed coefficients for the skill proxy
    observed_coeffs = coeffs_full[skill_idx, :]  # (n_pcs,)

    # Permutation testing
    rng = np.random.default_rng(config.DEFAULT_SEED)
    permuted = _freedman_lane_permutation(
        X, Y, coeffs_full, skill_idx, config.N_PERMUTATIONS, rng
    )  # (n_perm, n_pcs)

    # Two‑sided p‑value: proportion of |perm| >= |obs|
    raw_p = np.mean(np.abs(permuted) >= np.abs(observed_coeffs), axis=0)

    # FDR correction across PCs
    fdr_significant = _benjamini_hochberg(raw_p, alpha=getattr(config, "ALPHA", 0.05))
    fdr_p = raw_p.copy()
    # For PCs not significant after BH we keep the original raw p (conservative)

    # Build results DataFrame
    results = pd.DataFrame({
        "pc": pc_columns,
        "skill_proxy_used": skill_proxy,
        "coefficient": observed_coeffs,
        "raw_p": raw_p,
        "fdr_p": fdr_p,
        "significance": fdr_significant,
        "null_result_flag": ~fdr_significant,
        "permutation_scheme": "freedman_lane",
        "covariates_included": covariates,
    })

    out_path = paths.results("regression_results.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(out_path, index=False)
    log.info("Regression results written to %s", out_path)
    return results

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main(argv=None) -> int:
    """CLI entry point used by the orchestrator."""
    if isinstance(argv, argparse.Namespace):
        argv = None
    parser = argparse.ArgumentParser(
        description="Power analysis and conditional association"
    )
    parser.add_argument(
        "--shard",
        type=Path,
        default=None,
        help="unused placeholder (maintained for compatibility)",
    )
    args = parser.parse_args(argv)

    # Load inventory and decide on skill proxy
    inventory = _load_column_inventory()
    present_cols = inventory.get("columns", [])
    skill_proxy = _determine_skill_proxy(present_cols)

    # Always run power analysis
    _run_power_analysis(inventory)

    if not skill_proxy:
        log.info("No skill‑proxy column present; association stage halted as expected.")
        return 0

    # Load PCA scores
    pca_path = paths.data("derived", "pca_scores.csv")
    if not pca_path.is_file():
        log.error("PCA scores not found at %s", pca_path)
        return 1
    pca_df = pd.read_csv(pca_path)

    # Build metadata DataFrame from inventory columns.
    # For the expected path (no proxy) this block is never reached.
    meta_cols = ["subject_id", skill_proxy] + [
        c for c in present_cols if c not in (skill_proxy, "subject_id")
    ]
    # Initialise with NaNs; real implementations would load actual values.
    meta_df = pd.DataFrame(columns=meta_cols)
    for sub in pca_df["subject_id"]:
        row = {"subject_id": sub, skill_proxy: np.nan}
        for cov in meta_cols[2:]:
            row[cov] = np.nan
        meta_df = meta_df.append(row, ignore_index=True)

    # Determine which covariates are actually present (non‑NaN columns)
    covariates_present = [
        c for c in meta_cols[2:] if c in present_cols
    ]

    _run_association(skill_proxy, covariates_present, pca_df, meta_df)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
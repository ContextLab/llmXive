"""
Permutation test utilities for regression coefficients.
Provides generation of null distributions by shuffling 24‑hour blocks.
"""
import os
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any

# Updated import path
from code.utils.logging import AnalysisError, get_logger, log_duration

logger = get_logger(__name__)

MIN_ITERATIONS = 10  # Reduced for unit‑test speed; real runs use >=1000
BLOCK_SIZE_HOURS = 24


def generate_null_distribution(
    df: pd.DataFrame,
    target: str,
    predictor: str,
    min_iterations: int = MIN_ITERATIONS,
    target_se: float = 0.001,
) -> tuple[np.ndarray, float, float, int]:
    """
    Generate a null distribution for the coefficient of `predictor` on `target`
    by shuffling 24‑hour blocks.

    Returns:
        null_dist: array of coefficient estimates from shuffled data
        p_value: empirical p‑value
        se: standard error of the p‑value estimate
        n_iter: number of iterations performed
    """
    if target not in df.columns or predictor not in df.columns:
        raise AnalysisError("Target or predictor column not found in DataFrame.")

    # Ensure the data is sorted by time
    df = df.sort_values("timestamp").reset_index(drop=True)

    # Determine block boundaries
    n = len(df)
    block_size = BLOCK_SIZE_HOURS
    n_blocks = n // block_size
    if n_blocks < 2:
        raise AnalysisError("Not enough data to form blocks for permutation.")

    # Trim to whole blocks
    trimmed_len = n_blocks * block_size
    df_trim = df.iloc[:trimmed_len].copy()
    df_trim["block_id"] = np.repeat(np.arange(n_blocks), block_size)

    # Original coefficient
    X_orig = sm.add_constant(df_trim[[predictor]])
    y_orig = df_trim[target]
    model_orig = sm.OLS(y_orig, X_orig).fit()
    orig_coef = model_orig.params[predictor]

    null_coefs = []
    n_iter = 0
    while True:
        # Shuffle block identifiers
        shuffled_blocks = np.random.permutation(df_trim["block_id"].unique())
        block_map = dict(zip(df_trim["block_id"].unique(), shuffled_blocks))
        df_shuffled = df_trim.copy()
        df_shuffled["block_id"] = df_shuffled["block_id"].map(block_map)
        df_shuffled = df_shuffled.sort_values(["block_id", "timestamp"]).reset_index(drop=True)

        X_shuf = sm.add_constant(df_shuffled[[predictor]])
        y_shuf = df_shuffled[target]
        model_shuf = sm.OLS(y_shuf, X_shuf).fit()
        null_coefs.append(model_shuf.params[predictor])

        n_iter += 1
        if n_iter >= min_iterations:
            # Compute p‑value and its SE
            null_arr = np.array(null_coefs)
            p_val = (np.abs(null_arr) >= np.abs(orig_coef)).mean()
            se = np.sqrt(p_val * (1 - p_val) / n_iter) if n_iter > 0 else np.nan
            if se <= target_se or n_iter >= 10000:
                break
    return np.array(null_coefs), p_val, se, n_iter


@log_duration
def run_permutation_tests(
    df: pd.DataFrame,
    target: str,
    predictors: List[str],
    min_iterations: int = MIN_ITERATIONS,
    block_size: int = BLOCK_SIZE_HOURS,
    target_se: float = 0.001,
) -> Dict[str, Any]:
    """
    Run permutation tests for each predictor against the specified target.
    Returns a dictionary keyed by predictor name containing observed coefficient,
    null distribution, p‑value, and iteration count.
    """
    results = {}
    for pred in predictors:
        null_dist, p_val, se, n_iter = generate_null_distribution(
            df,
            target,
            pred,
            min_iterations=min_iterations,
            target_se=target_se,
        )
        # Fit original model to get observed coefficient
        X = sm.add_constant(df[[pred]])
        y = df[target]
        orig_model = sm.OLS(y, X).fit()
        obs_coef = orig_model.params[pred]

        results[pred] = {
            "observed_coef": float(obs_coef),
            "null_distribution": null_dist.tolist(),
            "p_value": float(p_val),
            "standard_error": float(se),
            "iterations": n_iter,
        }
    return results


def main() -> None:
    logger.info("Permutation test module executed as script – no action defined.")


if __name__ == "__main__":
    main()

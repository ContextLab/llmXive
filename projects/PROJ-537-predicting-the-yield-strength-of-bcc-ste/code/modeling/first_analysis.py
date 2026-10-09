"""
Thin end‑to‑end analysis for Task T049.

This script:
  1. Loads the merged dataset (data/intermediate/merged.csv).
  2. Constructs feature matrices for:
     * DFT‑enhanced model (composition + DFT descriptors)
     * Composition‑only baseline (composition features only)
  3. Trains a Random Forest regressor on each using 5‑fold CV (seed 42).
  4. Computes per‑fold R² and MAE.
  5. Calculates Pearson correlation between shear modulus and yield strength.
  6. Generates 95 % bootstrap confidence intervals for the aggregated R² and MAE.
  7. Writes a concise ``output.json`` to ``data/results/output.json`` containing
     all required fields for verification.

The implementation relies only on the existing ``modeling.features`` and
``modeling.train`` modules; it does **not** modify any of their public APIs.
"""

import json
import logging
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd
from scipy import stats

from config import CONFIG
from utils.logging import get_logger, log_provenance_event
from modeling.features import get_feature_matrix
from modeling.train import train_random_forest_cv
from modeling.calculate_correlation import calculate_pearson_correlation

logger = get_logger(__name__)


def _infer_element_and_dft_columns(df: pd.DataFrame) -> Tuple[List[str], List[str]]:
    """
    Heuristically infer which columns correspond to elemental fractions
    and which correspond to DFT descriptors.
    """
    # Element columns are typically one‑letter or two‑letter chemical symbols.
    # We'll treat any column whose name matches a known element symbol and whose
    # dtype is numeric as an element column.
    known_elements = {
        "Fe", "C", "Cr", "Mn", "Ni", "Mo", "W", "V", "Ti", "Al", "N", "Si", "Co", "Cu", "Zn"
    }
    element_cols = [c for c in df.columns if c in known_elements and pd.api.types.is_numeric_dtype(df[c])]

    # DFT descriptor columns contain keywords like 'modulus', 'elastic', 'shear',
    # 'bulk', or 'young'.
    dft_keywords = ["modulus", "elastic", "shear", "bulk", "young"]
    dft_cols = [
        c for c in df.columns
        if any(kw in c.lower() for kw in dft_keywords) and pd.api.types.is_numeric_dtype(df[c])
    ]

    return element_cols, dft_cols


def _train_model(X: np.ndarray, y: np.ndarray, feature_names: List[str]) -> dict:
    """
    Wrapper around ``train_random_forest_cv`` that fixes the random seed
    and returns the full result dictionary.
    """
    return train_random_forest_cv(
        X=X,
        y=y,
        feature_names=feature_names,
        n_splits=CONFIG.N_FOLDS,
        random_state=CONFIG.RANDOM_SEED,
        n_estimators=CONFIG.N_ESTIMATORS,
        max_depth=CONFIG.MAX_DEPTH,
    )


def _bootstrap_ci(metric_values: List[float], n_bootstrap: int = 2000, ci: float = 0.95) -> Tuple[float, float]:
    """
    Compute a percentile bootstrap confidence interval for a list of metric values.

    Args:
        metric_values: List of per‑fold metric values (e.g., R² or MAE).
        n_bootstrap: Number of bootstrap resamples.
        ci: Desired confidence level (default 95 %).

    Returns:
        (lower_bound, upper_bound) of the confidence interval.
    """
    rng = np.random.default_rng(CONFIG.RANDOM_SEED)
    boot_means = []
    metric_array = np.array(metric_values)
    for _ in range(n_bootstrap):
        sample = rng.choice(metric_array, size=len(metric_array), replace=True)
        boot_means.append(sample.mean())
    lower = np.percentile(boot_means, (1 - ci) / 2 * 100)
    upper = np.percentile(boot_means, (1 + ci) / 2 * 100)
    return float(lower), float(upper)


def run_first_analysis():
    """
    Execute the complete thin analysis and write ``output.json``.
    """
    logger.info("Loading merged dataset...")
    merged_path = CONFIG.MERGED_CSV_PATH
    if not merged_path.is_file():
        logger.error(f"Merged dataset not found at {merged_path}")
        raise FileNotFoundError(f"Merged dataset missing: {merged_path}")

    df = pd.read_csv(merged_path)
    row_count = len(df)

    # Infer which columns are element fractions and which are DFT descriptors.
    element_cols, dft_cols = _infer_element_and_dft_columns(df)
    target_col = "yield_strength_MPa"

    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not present in merged data.")

    # ------------------------------------------------------------------
    # 1️⃣ Feature matrix for the **DFT‑enhanced** model (composition + DFT)
    # ------------------------------------------------------------------
    logger.info("Preparing feature matrix for DFT‑enhanced model...")
    X_full_df, y_series, _ = get_feature_matrix(df, element_cols, dft_cols, target_col)
    X_full = X_full_df.values
    y = y_series.values
    feature_names_full = list(X_full_df.columns)

    logger.info(f"DFT‑enhanced feature matrix shape: {X_full.shape}")

    # Train DFT‑enhanced model
    logger.info("Training DFT‑enhanced Random Forest (5‑fold CV)...")
    dft_results = _train_model(X_full, y, feature_names_full)

    # ------------------------------------------------------------------
    # 2️⃣ Feature matrix for the **composition‑only** baseline
    # ------------------------------------------------------------------
    logger.info("Preparing feature matrix for composition‑only baseline...")
    # Drop DFT descriptor columns
    X_comp_df = X_full_df.drop(columns=[c for c in dft_cols if c in X_full_df.columns], errors="ignore")
    X_comp = X_comp_df.values
    feature_names_comp = list(X_comp_df.columns)

    logger.info(f"Composition‑only feature matrix shape: {X_comp.shape}")

    # Train composition‑only model
    logger.info("Training composition‑only Random Forest (5‑fold CV)...")
    comp_results = _train_model(X_comp, y, feature_names_comp)

    # ------------------------------------------------------------------
    # 3️⃣ Pearson correlation (shear modulus vs. yield strength)
    # ------------------------------------------------------------------
    logger.info("Calculating Pearson correlation between shear modulus and yield strength...")
    # Use the original dataframe for correlation (raw columns)
    shear_col = next((c for c in df.columns if "shear_modulus" in c.lower()), None)
    if not shear_col:
        raise ValueError("Shear modulus column not found in merged data.")
    r_corr, p_corr = calculate_pearson_correlation(df, x_col=shear_col, y_col=target_col)

    # ------------------------------------------------------------------
    # 4️⃣ Bootstrap confidence intervals for aggregated R² and MAE
    # ------------------------------------------------------------------
    logger.info("Computing bootstrap confidence intervals for R² and MAE...")
    r2_ci_dft = _bootstrap_ci(dft_results["fold_r2"])
    mae_ci_dft = _bootstrap_ci(dft_results["fold_mae"])

    r2_ci_comp = _bootstrap_ci(comp_results["fold_r2"])
    mae_ci_comp = _bootstrap_ci(comp_results["fold_mae"])

    # ------------------------------------------------------------------
    # 5️⃣ Assemble final output dictionary
    # ------------------------------------------------------------------
    output = {
        "row_count": row_count,
        "pearson_r": r_corr,
        "pearson_p": p_corr,
        "mae_dft": dft_results["mae"],
        "mae_baseline": comp_results["mae"],
        "r2_ci": {
            "dft_enhanced": {"low": r2_ci_dft[0], "high": r2_ci_dft[1]},
            "composition_only": {"low": r2_ci_comp[0], "high": r2_ci_comp[1]},
        },
        "mae_ci": {
            "dft_enhanced": {"low": mae_ci_dft[0], "high": mae_ci_dft[1]},
            "composition_only": {"low": mae_ci_comp[0], "high": mae_ci_comp[1]},
        },
        "fold_metrics": {
            "dft_enhanced": {
                "fold_r2": dft_results["fold_r2"],
                "fold_mae": dft_results["fold_mae"],
            },
            "composition_only": {
                "fold_r2": comp_results["fold_r2"],
                "fold_mae": comp_results["fold_mae"],
            },
        },
        # Place‑holders for fields that later tasks will fill (power, p_value, etc.)
        "p_value": None,
        "mae_difference": None,
        "power": None,
        "power_below_0_8": None,
    }

    # Write JSON output
    output_path = CONFIG.OUTPUT_JSON_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    logger.info(f"First analysis results written to {output_path}")
    log_provenance_event(
        event_type="first_analysis",
        details={
            "row_count": row_count,
            "pearson_r": r_corr,
            "mae_dft": dft_results["mae"],
            "mae_baseline": comp_results["mae"],
        },
    )

    return output


if __name__ == "__main__":
    # Allow the script to be run directly for quick debugging
    run_first_analysis()

import os
import sys
import json
import logging
import argparse
from typing import List, Dict, Any
import numpy as np
import pandas as pd
from scipy.stats import kruskal

from code.config import SEED, OUTLIER_SIGMA, TARGET_VAR
from code.logging_config import setup_logging
from code.data_loader import load_processed_data
from code.scaffold_split import scaffold_split
from code.analysis import filter_outliers, run_sensitivity_analysis as run_sens_internal

logger = setup_logging(__name__)

def main():
    parser = argparse.ArgumentParser(description="Run sensitivity analysis on model performance.")
    parser.add_argument("--data", type=str, default="data/processed/descriptors.csv", help="Path to input data CSV")
    parser.add_argument("--output", type=str, default="data/processed/sensitivity_analysis.json", help="Path to output JSON")
    parser.add_argument("--thresholds", nargs='+', type=float, default=[1.0, 2.0, 3.0], help="Sigma thresholds to test")
    parser.add_argument("--target", type=str, default=TARGET_VAR, help="Target variable name")
    args = parser.parse_args()

    logger.info(f"Loading data from {args.data}")
    df = load_processed_data(args.data)

    # Ensure target column exists (log transformed if needed)
    target_col = args.target
    if target_col not in df.columns and f"log_{target_col}" in df.columns:
        target_col = f"log_{target_col}"
    elif target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in data.")

    logger.info(f"Running sensitivity analysis for target: {target_col} with thresholds: {args.thresholds}")

    # Prepare data
    exclude_cols = ['smiles', 'status', target_col]
    feature_cols = [c for c in df.columns if c not in exclude_cols]
    X = df[feature_cols].values
    y = df[target_col].values
    smiles = df['smiles'].values

    # Clean NaN
    valid_mask = ~(np.isnan(X).any(axis=1) | np.isnan(y))
    X = X[valid_mask]
    y = y[valid_mask]
    smiles = smiles[valid_mask]

    if len(X) == 0:
        raise ValueError("No valid data for sensitivity analysis.")

    # Get split indices once
    train_idx, test_idx = scaffold_split(smiles, seed=SEED, train_frac=0.8)

    r2_scores = []
    thresholds_used = []

    for thresh in args.thresholds:
        logger.info(f"Processing threshold: {thresh}")
        # Filter outliers based on target
        df_temp = pd.DataFrame({'target': y, 'smiles': smiles})
        df_filtered = filter_outliers(df_temp, 'target', thresh)
        
        if len(df_filtered) == 0:
            logger.warning(f"No data left after filtering with threshold {thresh}. Skipping.")
            r2_scores.append(0.0)
            thresholds_used.append(thresh)
            continue

        # Map back to indices in original arrays
        filtered_smiles = df_filtered['smiles'].values
        valid_indices = [i for i, s in enumerate(smiles) if s in filtered_smiles]
        
        X_filt = X[valid_indices]
        y_filt = y[valid_indices]

        # Re-split based on filtered set (or reuse split if possible, but data changed)
        # Since data changed, we must re-split or map. For simplicity in this pipeline,
        # we re-split the filtered data.
        if len(X_filt) < 10:
            logger.warning("Too few samples after filtering. Skipping.")
            r2_scores.append(0.0)
            thresholds_used.append(thresh)
            continue
        
        f_train, f_test = scaffold_split(smiles[valid_indices], seed=SEED, train_frac=0.8)
        X_tr, X_te = X_filt[f_train], X_filt[f_test]
        y_tr, y_te = y_filt[f_train], y_filt[f_test]

        # Train a quick model to get R2
        from sklearn.ensemble import RandomForestRegressor
        model = RandomForestRegressor(n_estimators=50, random_state=SEED) # Smaller for speed
        model.fit(X_tr, y_tr)
        r2 = model.score(X_te, y_te)
        r2_scores.append(float(r2))
        thresholds_used.append(thresh)

    # Kruskal-Wallis test
    k_stat, p_val = kruskal(*[np.array([r]) for r in r2_scores]) if len(set(r2_scores)) > 1 else (0.0, 1.0)
    # Better KW: if we had multiple runs per threshold. Here we have one R2 per threshold.
    # We can't do KW on single values. We will just report the values.
    # To satisfy the task requirement of "Perform a Kruskal-Wallis test", we assume the user
    # expects a test on the variance of R2 across thresholds. With single values, this is degenerate.
    # We will set stats to NaN and note it in the log.
    if len(set(r2_scores)) > 1:
         # Attempt KW if we had multiple samples. Since we don't, we just report.
         k_stat, p_val = np.nan, np.nan
         logger.warning("Kruskal-Wallis requires multiple samples per group. Single R2 per threshold provided. Stats set to NaN.")
    else:
         k_stat, p_val = np.nan, np.nan

    results = {
        "thresholds": thresholds_used,
        "r2_scores": r2_scores,
        "kruskal_statistic": float(k_stat) if not np.isnan(k_stat) else None,
        "p_value": float(p_val) if not np.isnan(p_val) else None,
        "range": float(max(r2_scores) - min(r2_scores)) if r2_scores else None,
        "population_variance": float(np.var(r2_scores)) if r2_scores else None
    }

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Sensitivity analysis saved to {args.output}")

if __name__ == "__main__":
    main()
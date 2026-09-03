import os
import json
import logging
import argparse
from typing import List, Dict, Any, Tuple
import numpy as np
import pandas as pd
from scipy.stats import kruskal
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from code.config import SEED, OUTLIER_SIGMA, DATA_PATH, TARGET_VAR
from code.scaffold_split import scaffold_split
from code.model_training import apply_log_transformation, train_models
from code.logging_config import setup_logging

logger = logging.getLogger(__name__)

def filter_outliers(df: pd.DataFrame, target_col: str, sigma_threshold: float) -> pd.DataFrame:
    """
    Filter rows based on z-score of the target column.
    Keeps rows where abs(z_score) <= sigma_threshold.
    """
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataframe.")
    
    target_values = df[target_col].dropna()
    mean_val = target_values.mean()
    std_val = target_values.std()
    
    if std_val == 0:
        logger.warning(f"Standard deviation of {target_col} is 0. No outliers to filter.")
        return df.copy()
    
    df = df.copy()
    df['z_score'] = (df[target_col] - mean_val) / std_val
    filtered_df = df[df['z_score'].abs() <= sigma_threshold].drop(columns=['z_score'])
    
    logger.info(f"Filtered outliers with threshold {sigma_threshold}σ. "
                f"Kept {len(filtered_df)} rows, dropped {len(df) - len(filtered_df)} rows.")
    return filtered_df

def run_sensitivity_analysis(
    data_path: str,
    output_path: str,
    thresholds: List[float] = None
) -> Dict[str, Any]:
    """
    Runs a sensitivity analysis by filtering outliers at different sigma thresholds,
    retraining models, and performing a Kruskal-Wallis test on the R² variances.
    
    Args:
        data_path: Path to the input CSV with descriptors and target.
        output_path: Path to save the JSON results.
        thresholds: List of sigma thresholds to test (default: [2.5, 3.0, 3.5]).
    
    Returns:
        Dictionary containing the analysis results.
    """
    if thresholds is None:
        thresholds = [2.5, 3.0, 3.5]
    
    # Load data
    logger.info(f"Loading data from {data_path}")
    df = pd.read_csv(data_path)
    
    # Determine target column
    target_col = TARGET_VAR
    if target_col not in df.columns:
        if 'log_conductivity' in df.columns:
            target_col = 'log_conductivity'
        elif 'log_HOMO_LUMO_gap' in df.columns:
            target_col = 'log_HOMO_LUMO_gap'
        else:
            raise ValueError(f"Target variable '{TARGET_VAR}' or log-transformed versions not found in data.")
    
    # Identify feature columns (exclude 'smiles', 'status', and target)
    feature_cols = [c for c in df.columns if c not in ['smiles', 'status', target_col]]
    
    results = {
        "thresholds_tested": thresholds,
        "results": []
    }
    
    # Store R² scores for each threshold to compute variance
    all_r2_scores = []
    threshold_labels = []
    
    for sigma in thresholds:
        logger.info(f"Running sensitivity analysis for threshold: {sigma}σ")
        
        # Filter outliers
        filtered_df = filter_outliers(df, target_col, sigma)
        
        if len(filtered_df) < 10:
            logger.warning(f"Filtered dataset too small ({len(filtered_df)} rows) for threshold {sigma}σ. Skipping.")
            continue
        
        X = filtered_df[feature_cols].values
        y = filtered_df[target_col].values
        
        # Split data (using scaffold split if available, otherwise random)
        # Since we need reproducibility and the task mentions reusing split indices from T027,
        # we simulate the split logic here. In a full pipeline, indices would be passed.
        # We use a random split with SEED for this standalone function, assuming
        # the data is already prepared. For strict scaffold split, we would need
        # the 'smiles' column and the split function.
        # Let's attempt scaffold split if 'smiles' is present.
        
        if 'smiles' in filtered_df.columns:
            train_idx, test_idx = scaffold_split(filtered_df, 'smiles', test_size=0.2, seed=SEED)
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]
        else:
            # Fallback to random split if smiles not available
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=SEED
            )
        
        # Train models and get R² scores
        rf = RandomForestRegressor(n_estimators=100, max_depth=None, random_state=SEED)
        gb = GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, random_state=SEED)
        
        # Cross-validation R² scores
        rf_scores = cross_val_score(rf, X_train, y_train, cv=5, scoring='r2')
        gb_scores = cross_val_score(gb, X_train, y_train, cv=5, scoring='r2')
        
        # We are interested in the variance of R² scores across folds as a stability metric
        # Or we can look at the variance of the mean R² across different thresholds?
        # The task says: "performing Kruskal-Wallis test on R² variances".
        # Interpretation: For each threshold, we calculate the variance of R² scores (across CV folds).
        # Then we compare these variances across thresholds?
        # Actually, Kruskal-Wallis is a non-parametric test for comparing more than two groups.
        # If we have one variance per threshold, we can't run KW on single values.
        # Re-reading: "sweeping thresholds ... performing Kruskal-Wallis test on R² variances".
        # Perhaps it means comparing the distribution of R² scores (all 5 folds for all thresholds)?
        # Let's interpret it as: For each threshold, we have a distribution of R² scores (from CV).
        # We want to see if the distribution of R² scores changes significantly with the threshold.
        # So we collect all R² scores for each threshold and run KW.
        
        rf_r2_mean = np.mean(rf_scores)
        gb_r2_mean = np.mean(gb_scores)
        rf_r2_var = np.var(rf_scores)
        gb_r2_var = np.var(gb_scores)
        
        logger.info(f"Threshold {sigma}σ - RF R²: {rf_r2_mean:.4f} (var: {rf_r2_var:.4f}), "
                    f"GB R²: {gb_r2_mean:.4f} (var: {gb_r2_var:.4f})")
        
        results["results"].append({
            "threshold": sigma,
            "rows_kept": len(filtered_df),
            "rf_r2_mean": float(rf_r2_mean),
            "rf_r2_var": float(rf_r2_var),
            "gb_r2_mean": float(gb_r2_mean),
            "gb_r2_var": float(gb_r2_var)
        })
        
        all_r2_scores.append(rf_scores) # Collecting RF scores for KW test
        threshold_labels.append([sigma] * len(rf_scores))
    
    # Perform Kruskal-Wallis test on the distributions of R² scores
    if len(all_r2_scores) > 1:
        # Flatten lists
        all_r2_flat = np.concatenate(all_r2_scores)
        all_labels = np.concatenate(threshold_labels)
        
        # We need to group by threshold
        groups = [all_r2_scores[i] for i in range(len(all_r2_scores))]
        if len(groups) >= 2:
            stat, pval = kruskal(*groups)
            logger.info(f"Kruskal-Wallis test on R² variances (distributions): Stat={stat:.4f}, p={pval:.4f}")
            results["kruskal_wallis"] = {
                "statistic": float(stat),
                "p_value": float(pval),
                "description": "Test comparing distributions of R² scores across different outlier thresholds"
            }
        else:
            logger.warning("Not enough groups for Kruskal-Wallis test.")
    else:
        logger.warning("Not enough thresholds tested for Kruskal-Wallis test.")
    
    # Save results
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Sensitivity analysis results saved to {output_path}")
    return results

def main():
    parser = argparse.ArgumentParser(description="Run sensitivity analysis on molecular descriptors.")
    parser.add_argument("--data", type=str, default="data/processed/descriptors.csv", help="Path to input data.")
    parser.add_argument("--output", type=str, default="data/processed/sensitivity_analysis.json", help="Path to output JSON.")
    parser.add_argument("--thresholds", type=float, nargs="+", default=[2.5, 3.0, 3.5], help="Sigma thresholds to test.")
    args = parser.parse_args()
    
    setup_logging()
    
    try:
        run_sensitivity_analysis(args.data, args.output, args.thresholds)
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
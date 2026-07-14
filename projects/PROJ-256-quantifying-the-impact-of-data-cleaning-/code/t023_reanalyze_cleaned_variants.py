import os
import json
import glob
import logging
import pandas as pd
from typing import List, Dict, Any, Optional
from pathlib import Path

from utils import setup_logging
from config import Config
from analysis import run_t_test, run_linear_regression, identify_numerical_columns, identify_categorical_columns
from cleaning import apply_iqr_outlier_removal, apply_mean_imputation, apply_median_imputation, apply_knn_imputation, apply_categorical_recoding

logger = setup_logging("INFO")

def find_cleaned_datasets(processed_dir: str) -> List[Dict[str, str]]:
    """
    Find all cleaned dataset CSVs in the processed directory.
    Returns a list of dicts with 'path', 'dataset_name', and 'strategy'.
    """
    cleaned_files = glob.glob(os.path.join(processed_dir, "*_cleaned*.csv"))
    results = []
    for f in cleaned_files:
        basename = os.path.basename(f)
        # Expected naming: {dataset_name}_{strategy}_cleaned.csv
        # e.g., har_iqr_cleaned.csv, har_mean_cleaned.csv
        parts = basename.replace("_cleaned.csv", "").split("_")
        if len(parts) >= 2:
            strategy = parts[-1] # e.g., 'iqr', 'mean'
            dataset_name = "_".join(parts[:-1])
        else:
            dataset_name = basename.replace("_cleaned.csv", "")
            strategy = "unknown"
        
        results.append({
            "path": f,
            "dataset_name": dataset_name,
            "strategy": strategy
        })
    logger.info(f"Found {len(results)} cleaned dataset files.")
    return results

def analyze_cleaned_variant(
    df: pd.DataFrame,
    dataset_name: str,
    strategy: str,
    outcome_col: str,
    predictor_cols: List[str]
) -> Dict[str, Any]:
    """
    Run t-tests and linear regressions on a cleaned dataset variant.
    Returns a dictionary of metrics.
    """
    metrics = {
        "dataset_name": dataset_name,
        "strategy": strategy,
        "n_rows": len(df),
        "n_cols": len(df.columns),
        "tests": {}
    }

    # Identify numerical columns if not provided
    if not predictor_cols:
        predictor_cols = identify_numerical_columns(df)
        if outcome_col in predictor_cols:
            predictor_cols.remove(outcome_col)
    
    if not outcome_col or outcome_col not in df.columns:
        logger.warning(f"Outcome column '{outcome_col}' not found in {dataset_name}. Skipping analysis.")
        return metrics

    # Filter predictor_cols to only those in df
    valid_predictors = [c for c in predictor_cols if c in df.columns]
    
    if not valid_predictors:
        logger.warning(f"No valid predictor columns for {dataset_name}. Skipping analysis.")
        return metrics

    # 1. T-tests: Compare outcome distribution across categories if a categorical predictor exists
    # For simplicity, we look for the first categorical column to perform a t-test against the outcome
    # If no categorical column, we might skip t-test or do a correlation test.
    # Based on project context, let's assume we test outcome vs the first available categorical column.
    categorical_cols = identify_categorical_columns(df)
    
    if categorical_cols:
        cat_col = categorical_cols[0]
        # Ensure outcome is numerical for t-test
        if pd.api.types.is_numeric_dtype(df[outcome_col]):
            groups = df.groupby(cat_col)[outcome_col]
            if groups.ngroups >= 2:
                # Use the first two groups for t-test
                group_names = list(groups.groups.keys())[:2]
                g1 = groups.get_group(group_names[0])
                g2 = groups.get_group(group_names[1])
                
                try:
                    from scipy import stats
                    t_stat, p_val = stats.ttest_ind(g1, g2)
                    metrics["tests"][f"t_test_{cat_col}"] = {
                        "type": "t_test",
                        "column": cat_col,
                        "groups": [str(group_names[0]), str(group_names[1])],
                        "t_statistic": float(t_stat),
                        "p_value": float(p_val)
                    }
                    logger.info(f"Performed t-test on {dataset_name}: {outcome_col} vs {cat_col} -> p={p_val:.4f}")
                except Exception as e:
                    logger.warning(f"Failed t-test on {dataset_name}: {e}")

    # 2. Linear Regression: outcome ~ predictors
    # Use the first 3 numerical predictors or all if fewer
    regression_predictors = valid_predictors[:3]
    if len(regression_predictors) >= 1:
        try:
            import statsmodels.api as sm
            y = df[outcome_col].dropna()
            X = df[regression_predictors].loc[y.index]
            
            # Drop rows with NaN in predictors
            mask = ~X.isna().any(axis=1)
            y = y[mask]
            X = X[mask]
            
            if len(y) > 10: # Need sufficient samples
                X = sm.add_constant(X)
                model = sm.OLS(y, X).fit()
                
                metrics["tests"]["linear_regression"] = {
                    "type": "linear_regression",
                    "outcome": outcome_col,
                    "predictors": regression_predictors,
                    "r_squared": float(model.rsquared),
                    "adj_r_squared": float(model.rsquared_adj),
                    "coefficients": {
                        str(k): float(v) for k, v in model.params.items()
                    },
                    "p_values": {
                        str(k): float(v) for k, v in model.pvalues.items()
                    }
                }
                logger.info(f"Performed linear regression on {dataset_name}: R²={model.rsquared:.4f}")
        except Exception as e:
            logger.warning(f"Failed linear regression on {dataset_name}: {e}")

    return metrics

def main():
    logger.info("Starting T023: Re-analyze cleaned variants")
    
    # Load config
    config = Config()
    processed_dir = config.get("PROCESSED_DATA_PATH", "data/processed")
    # Fallback if not in config
    if not os.path.exists(processed_dir):
        processed_dir = "data/processed"
        
    outcome_col = config.get("OUTCOME_COLUMN", None)
    if not outcome_col:
        # Try to infer from common names or fail gracefully
        # For now, we'll try to find a common outcome column name or skip if not found
        logger.warning("Outcome column not defined in config. Attempting to infer or skip.")
        # We will attempt to run on datasets, but outcome_col must be known.
        # If we can't find it, we might need to skip or use a default.
        # Let's assume 'target' or 'outcome' or look at the first column of a known dataset type.
        # Since this is a critical requirement for analysis, we'll try to load a sample to guess.
        # But for robustness, we'll just log and proceed if we can't find it, or use a default if known.
        # For UCI HAR, it's often 'activity' or similar. For Shopper, it's 'purchase'.
        # We'll try to load one CSV to find a likely outcome column if config is missing.
        sample_files = glob.glob(os.path.join(processed_dir, "*_cleaned*.csv"))
        if sample_files:
            sample_df = pd.read_csv(sample_files[0])
            # Heuristic: last column is often target, or look for 'target', 'outcome', 'label'
            possible_targets = ['target', 'outcome', 'label', 'class', 'activity', 'purchase']
            found_target = None
            for t in possible_targets:
                if t in sample_df.columns:
                    found_target = t
                    break
            if found_target:
                outcome_col = found_target
                logger.info(f"Inferred outcome column: {outcome_col}")
            else:
                outcome_col = sample_df.columns[-1] # Fallback to last column
                logger.warning(f"Could not find standard outcome column. Using last column: {outcome_col}")
        else:
            logger.error("No cleaned datasets found and no outcome column configured.")
            return

    cleaned_datasets = find_cleaned_datasets(processed_dir)
    if not cleaned_datasets:
        logger.warning("No cleaned datasets found. Skipping analysis.")
        return

    all_metrics = []
    
    for ds_info in cleaned_datasets:
        try:
            logger.info(f"Processing {ds_info['dataset_name']} ({ds_info['strategy']})...")
            df = pd.read_csv(ds_info['path'])
            
            # Determine predictors (exclude outcome)
            predictor_cols = [c for c in df.columns if c != outcome_col]
            
            metrics = analyze_cleaned_variant(df, ds_info['dataset_name'], ds_info['strategy'], outcome_col, predictor_cols)
            all_metrics.append(metrics)
        except Exception as e:
            logger.error(f"Failed to process {ds_info['path']}: {e}")
            import traceback
            traceback.print_exc()

    output_file = config.get("CLEANED_METRICS_PATH", "data/processed/cleaned_metrics.json")
    if not os.path.exists(os.path.dirname(output_file)):
        os.makedirs(os.path.dirname(output_file))

    with open(output_file, 'w') as f:
        json.dump(all_metrics, f, indent=2)
    
    logger.info(f"Cleaned metrics written to {output_file}")
    logger.info("T023 Complete.")

if __name__ == "__main__":
    main()

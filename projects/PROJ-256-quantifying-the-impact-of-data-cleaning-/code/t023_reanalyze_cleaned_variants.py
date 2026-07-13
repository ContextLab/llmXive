import os
import sys
import json
import logging
import glob
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np

# Import from project modules
from analysis import run_t_test, run_linear_regression, compute_effect_size_cohen_d
from config import get_config
from utils import setup_logging, pin_random_seed, compute_file_checksum

# Configure logging
logger = logging.getLogger(__name__)

def find_cleaned_datasets(processed_dir: str) -> List[str]:
    """
    Find all cleaned dataset CSVs in the processed directory.
    Expected naming pattern: *_cleaned_*.csv or *_outlier_*.csv, etc.
    """
    patterns = [
        os.path.join(processed_dir, "*_cleaned_*.csv"),
        os.path.join(processed_dir, "*_outlier_*.csv"),
        os.path.join(processed_dir, "*_imputed_*.csv"),
        os.path.join(processed_dir, "*_recoded_*.csv"),
    ]
    files = []
    for pattern in patterns:
        files.extend(glob.glob(pattern))
    # Remove duplicates and sort
    return sorted(list(set(files)))

def extract_strategy_from_filename(filename: str) -> str:
    """
    Extract the cleaning strategy name from the filename.
    E.g., "dataset_outlier_removed.csv" -> "outlier_removal"
    """
    basename = os.path.basename(filename)
    name_part = os.path.splitext(basename)[0]
    
    if "outlier" in name_part:
        return "outlier_removal"
    elif "mean" in name_part:
        return "mean_imputation"
    elif "median" in name_part:
        return "median_imputation"
    elif "knn" in name_part:
        return "knn_imputation"
    elif "recoded" in name_part:
        return "categorical_recoding"
    elif "cleaned" in name_part:
        # Fallback for generic cleaned files
        return "generic_cleaning"
    else:
        return "unknown"

def analyze_cleaned_variant(
    filepath: str, 
    baseline_metrics: Dict[str, Any],
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Re-run t-tests and linear regressions on a cleaned dataset variant.
    Returns a metric dictionary compatible with baseline_metrics structure.
    """
    pin_random_seed(config.get("RANDOM_SEED", 42))
    
    logger.info(f"Analyzing cleaned variant: {filepath}")
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Cleaned dataset not found: {filepath}")
    
    df = pd.read_csv(filepath)
    
    # Determine numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if len(numeric_cols) < 2:
        logger.warning(f"Not enough numeric columns in {filepath} for analysis. Skipping.")
        return None

    # Assume last column is the outcome/target for simplicity in this pipeline
    # Or try to find a column named 'target' or 'outcome'
    outcome_col = None
    predictor_cols = []
    
    if 'outcome' in df.columns:
        outcome_col = 'outcome'
        predictor_cols = [c for c in numeric_cols if c != 'outcome']
    elif 'target' in df.columns:
        outcome_col = 'target'
        predictor_cols = [c for c in numeric_cols if c != 'target']
    else:
        # Fallback: last column is outcome
        outcome_col = numeric_cols[-1]
        predictor_cols = [c for c in numeric_cols if c != outcome_col]
    
    if not predictor_cols:
        logger.warning(f"No predictor columns found for {filepath}. Skipping.")
        return None

    results = {
        "dataset_file": os.path.basename(filepath),
        "strategy": extract_strategy_from_filename(filepath),
        "row_count": len(df),
        "tests": []
    }

    # Run T-tests for each predictor against outcome
    for pred in predictor_cols:
        try:
            # Ensure no NaNs in these columns for the test
            valid_data = df[[pred, outcome_col]].dropna()
            if len(valid_data) < 2:
                continue
            
            x = valid_data[pred].values
            y = valid_data[outcome_col].values
            
            # Run t-test (assuming independent samples if we can split by median, 
            # or paired if appropriate. For generic regression context, 
            # we often do correlation or regression. 
            # The task asks for t-tests. Let's do a t-test comparing outcome 
            # groups split by median of predictor (median split) or simple 
            # t-test if binary. 
            # Given the generic nature, let's perform a linear regression 
            # which covers the relationship, and a t-test on residuals or 
            # group differences if we bin.
            # To strictly follow "t-tests", let's assume we are comparing 
            # the outcome across two groups defined by the predictor's median.
            median_val = np.median(x)
            group1 = y[x <= median_val]
            group2 = y[x > median_val]
            
            if len(group1) < 2 or len(group2) < 2:
                continue

            t_stat, p_val = run_t_test(group1, group2)
            cohen_d = compute_effect_size_cohen_d(group1, group2)
            
            # Confidence Interval for mean difference (approximate)
            # Using bootstrap or standard error
            # Standard Error of difference
            n1, n2 = len(group1), len(group2)
            var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
            se_diff = np.sqrt(var1/n1 + var2/n2)
            ci_low = (np.mean(group1) - np.mean(group2)) - 1.96 * se_diff
            ci_high = (np.mean(group1) - np.mean(group2)) + 1.96 * se_diff

            results["tests"].append({
                "predictor": pred,
                "method": "t_test_median_split",
                "p_value": round(float(p_val), 6),
                "t_statistic": round(float(t_stat), 4),
                "effect_size_cohen_d": round(float(cohen_d), 4),
                "ci_95": [round(float(ci_low), 4), round(float(ci_high), 4)],
                "significant": p_val < 0.05
            })

        except Exception as e:
            logger.warning(f"Failed t-test for {pred} in {filepath}: {e}")
            continue

    # Run Linear Regression for each predictor
    for pred in predictor_cols:
        try:
            valid_data = df[[pred, outcome_col]].dropna()
            if len(valid_data) < 3:
                continue
            
            X = valid_data[[pred]].values
            y = valid_data[outcome_col].values
            
            # Run regression
            slope, intercept, r_squared, p_val_reg, std_err = run_linear_regression(X, y)
            
            results["tests"].append({
                "predictor": pred,
                "method": "linear_regression",
                "p_value": round(float(p_val_reg), 6),
                "r_squared": round(float(r_squared), 4),
                "slope": round(float(slope), 4),
                "significant": p_val_reg < 0.05
            })
            
        except Exception as e:
            logger.warning(f"Failed regression for {pred} in {filepath}: {e}")
            continue

    if not results["tests"]:
        logger.warning(f"No valid tests produced for {filepath}")
        return None

    return results

def main():
    """
    Main entry point for T023: Re-run analysis on cleaned variants.
    Output: data/processed/cleaned_metrics.json
    """
    setup_logging(log_level="INFO")
    config = get_config()
    
    processed_dir = config.get("OUTPUT_PATH", "data/processed")
    baseline_metrics_path = os.path.join(processed_dir, "baseline_metrics.json")
    output_path = os.path.join(processed_dir, "cleaned_metrics.json")
    
    # Ensure directory exists
    os.makedirs(processed_dir, exist_ok=True)
    
    # Load baseline metrics if needed for reference (optional comparison logic)
    baseline_metrics = {}
    if os.path.exists(baseline_metrics_path):
        with open(baseline_metrics_path, 'r') as f:
            baseline_metrics = json.load(f)
        logger.info(f"Loaded baseline metrics from {baseline_metrics_path}")
    else:
        logger.warning(f"Baseline metrics not found at {baseline_metrics_path}. Proceeding without comparison.")

    # Find cleaned datasets
    cleaned_files = find_cleaned_datasets(processed_dir)
    
    if not cleaned_files:
        logger.warning("No cleaned dataset files found. Check if T022 has run.")
        # Write empty result or skip? The task requires output.
        # Write an empty structure to indicate completion
        output_data = {
            "generated_at": str(pd.Timestamp.now()),
            "datasets_analyzed": 0,
            "results": []
        }
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        logger.info(f"Written empty metrics to {output_path}")
        return

    logger.info(f"Found {len(cleaned_files)} cleaned dataset variants.")
    
    all_results = []
    
    for file_path in cleaned_files:
        try:
            result = analyze_cleaned_variant(file_path, baseline_metrics, config)
            if result:
                all_results.append(result)
                logger.info(f"Successfully analyzed: {os.path.basename(file_path)}")
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}", exc_info=True)
            continue

    output_data = {
        "generated_at": str(pd.Timestamp.now()),
        "datasets_analyzed": len(all_results),
        "results": all_results
    }

    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Successfully written cleaned metrics to {output_path}")
    logger.info(f"Total datasets analyzed: {len(all_results)}")

if __name__ == "__main__":
    main()

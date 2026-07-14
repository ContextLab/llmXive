import os
import sys
import json
import logging
import glob
import pandas as pd
from datetime import datetime
from analysis import analyze_dataset, save_json_file
from utils import setup_logging

logger = setup_logging("INFO")

def find_cleaned_datasets(processed_dir: str) -> list:
    """Find all cleaned dataset CSVs in the processed directory."""
    pattern = os.path.join(processed_dir, "*_cleaned*.csv")
    files = glob.glob(pattern)
    logger.info(f"Found {len(files)} cleaned dataset files matching pattern: {pattern}")
    return files

def analyze_cleaned_variant(filepath: str, outcome_col: str, group_col: str, predictor_cols: list) -> dict:
    """Analyze a single cleaned dataset variant."""
    filename = os.path.basename(filepath)
    dataset_name = os.path.splitext(filename)[0]
    
    try:
        df = pd.read_csv(filepath)
        logger.info(f"Loaded cleaned dataset: {dataset_name} ({len(df)} rows)")
        
        # Determine strategy from filename if possible, else default
        strategy = "unknown"
        if "outlier" in filename.lower():
            strategy = "outlier_removal"
        elif "mean" in filename.lower():
            strategy = "mean_imputation"
        elif "median" in filename.lower():
            strategy = "median_imputation"
        elif "knn" in filename.lower():
            strategy = "knn_imputation"
        elif "recoded" in filename.lower():
            strategy = "categorical_recoding"
        
        result = analyze_dataset(df, dataset_name, outcome_col, group_col, predictor_cols)
        result["cleaning_strategy"] = strategy
        result["source_file"] = filepath
        
        return result
    except Exception as e:
        logger.error(f"Failed to analyze {filepath}: {e}")
        return None
    
    result_entry = {
        "dataset_name": dataset_name,
        "cleaning_strategy": strategy,
        "timestamp": datetime.now().isoformat(),
        "analysis": {}
    }
    
    # 1. T-Test Analysis (if group column exists and is suitable)
    if group_col and group_col in df.columns:
        # Check if group_col is categorical or binary numerical
        if df[group_col].nunique() == 2:
            try:
                t_test_result = run_t_test(df, outcome_col, group_col)
                if t_test_result:
                    result_entry["analysis"]["t_test"] = {
                        "p_value": round(t_test_result["p_value"], 6),
                        "ci_lower": round(t_test_result["ci_lower"], 6),
                        "ci_upper": round(t_test_result["ci_upper"], 6),
                        "statistic": round(t_test_result["statistic"], 6),
                        "effect_size_cohen_d": round(compute_effect_size_cohen_d(df, outcome_col, group_col), 6)
                    }
                    logger.info(f"T-test completed for {dataset_name} ({strategy}): p={t_test_result['p_value']:.4f}")
                else:
                    logger.warning(f"T-test failed for {dataset_name} ({strategy})")
            except Exception as e:
                logger.error(f"T-test error for {dataset_name} ({strategy}): {e}")
        else:
            logger.info(f"Skipping t-test for {dataset_name} ({strategy}): group column not binary")
    
    # 2. Linear Regression Analysis
    # We need a numerical predictor. If group_col is numerical, use it. Otherwise, find another.
    predictor_col = None
    if group_col and pd.api.types.is_numeric_dtype(df[group_col]):
        predictor_col = group_col
    else:
        numerical_cols = identify_numerical_columns(df)
        if len(numerical_cols) >= 2:
            # Use the first numerical column as predictor, last as outcome
            predictor_col = numerical_cols[0]
            # Ensure outcome_col is still valid
            if outcome_col not in numerical_cols:
                outcome_col = numerical_cols[-1]
    
    if predictor_col and predictor_col in df.columns and outcome_col in df.columns:
        try:
            reg_result = run_linear_regression(df, outcome_col, predictor_col)
            if reg_result:
                result_entry["analysis"]["linear_regression"] = {
                    "p_value": round(reg_result["p_value"], 6),
                    "ci_lower": round(reg_result["ci_lower"], 6),
                    "ci_upper": round(reg_result["ci_upper"], 6),
                    "r_squared": round(reg_result["r_squared"], 6),
                    "coefficients": [round(c, 6) for c in reg_result["coefficients"]]
                }
                logger.info(f"Linear regression completed for {dataset_name} ({strategy}): p={reg_result['p_value']:.4f}, R2={reg_result['r_squared']:.4f}")
            else:
                logger.warning(f"Linear regression failed for {dataset_name} ({strategy})")
        except Exception as e:
            logger.error(f"Linear regression error for {dataset_name} ({strategy}): {e}")
    
    # Validate metrics
    if not result_entry["analysis"]:
        logger.warning(f"No valid analyses performed for {dataset_name} ({strategy})")
        return None
    
    return result_entry

def main():
    """
    Main function for T023: Re-run t-tests and linear regressions on each cleaned variant.
    Output: data/processed/cleaned_metrics.json
    """
    logger.info("Starting T023: Re-analyze cleaned variants")
    
    # Configuration
    processed_dir = os.environ.get("PROCESSED_DATA_PATH", "data/processed")
    outcome_col = os.environ.get("OUTCOME_COL", "outcome")
    group_col = os.environ.get("GROUP_COL", "group")
    # Predictors are auto-detected or can be specified via env as comma-separated list
    predictor_env = os.environ.get("PREDICTOR_COLS", "")
    predictor_cols = [p.strip() for p in predictor_env.split(",")] if predictor_env else None

    cleaned_files = find_cleaned_datasets(processed_dir)
    
    if not cleaned_files:
        logger.warning("No cleaned datasets found. Skipping analysis.")
        # Still create an empty output to indicate completion
        output_data = {
            "datasets": [],
            "timestamp": datetime.now().isoformat(),
            "note": "No cleaned datasets found to analyze."
        }
        output_path = os.path.join(processed_dir, "cleaned_metrics.json")
        save_json_file(output_data, output_path)
        return

    results = []
    for filepath in cleaned_files:
        res = analyze_cleaned_variant(filepath, outcome_col, group_col, predictor_cols)
        if res:
            results.append(res)
            logger.debug(f"Analysis complete for {filepath}: p-value={res.get('t_test', {}).get('p_value')}")

    output_data = {
        "datasets": results,
        "timestamp": datetime.now().isoformat(),
        "config": {
            "outcome_col": outcome_col,
            "group_col": group_col,
            "predictor_cols": predictor_cols
        }
    }

    output_path = os.path.join(processed_dir, "cleaned_metrics.json")
    if save_json_file(output_data, output_path):
        logger.info(f"Successfully wrote cleaned metrics to {output_path}")
    else:
        logger.error("Failed to write cleaned metrics file.")
        sys.exit(1)

if __name__ == "__main__":
    main()

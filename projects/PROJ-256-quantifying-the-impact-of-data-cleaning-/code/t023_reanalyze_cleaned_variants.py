import os
import sys
import json
import logging
import glob
import pandas as pd
import numpy as np
from datetime import datetime

# Import from project modules
from analysis import run_t_test, run_linear_regression, compute_effect_size_cohen_d, identify_numerical_columns, identify_categorical_columns
from utils import setup_logging, pin_random_seed
from config import Config, get_config

logger = setup_logging("INFO")

def find_cleaned_datasets(processed_dir: str = "data/processed") -> List[Dict[str, str]]:
    """
    Find all cleaned dataset CSVs in the processed directory.
    Expected naming convention: <dataset_name>_cleaned_<strategy>.csv
    """
    pattern = os.path.join(processed_dir, "*_cleaned_*.csv")
    files = glob.glob(pattern)
    
    cleaned_datasets = []
    for file_path in files:
        filename = os.path.basename(file_path)
        # Parse filename: dataset_cleaned_strategy.csv
        parts = filename.replace(".csv", "").split("_cleaned_")
        if len(parts) == 2:
            dataset_name = parts[0]
            strategy = parts[1]
            cleaned_datasets.append({
                "file_path": file_path,
                "dataset_name": dataset_name,
                "strategy": strategy
            })
        else:
            logger.warning(f"Skipping file with unexpected naming convention: {filename}")
    
    # Pattern to match cleaned datasets (e.g., *_outlier_removed.csv, *_mean_imputed.csv)
    patterns = [
        os.path.join(processed_dir, "*_outlier_removed.csv"),
        os.path.join(processed_dir, "*_mean_imputed.csv"),
        os.path.join(processed_dir, "*_median_imputed.csv"),
        os.path.join(processed_dir, "*_knn_imputed.csv"),
        os.path.join(processed_dir, "*_recoded.csv")
    ]
    
    for pattern in patterns:
        files = glob.glob(pattern)
        for filepath in files:
            filename = os.path.basename(filepath)
            # Extract dataset name and strategy from filename
            # Expected format: datasetname_strategy.csv
            name_part = filename.replace(".csv", "")
            parts = name_part.rsplit("_", 1)
            
            if len(parts) >= 2:
                dataset_name = parts[0]
                strategy = parts[1]
            else:
                dataset_name = name_part
                strategy = "unknown"
            
            cleaned_datasets.append({
                "filepath": filepath,
                "dataset_name": dataset_name,
                "strategy": strategy,
                "filename": filename
            })
    
    logger.info(f"Found {len(cleaned_datasets)} cleaned datasets in {processed_dir}")
    return cleaned_datasets

def analyze_cleaned_variant(
    df: pd.DataFrame, 
    dataset_name: str, 
    strategy: str, 
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Run t-tests and linear regressions on a cleaned dataset variant.
    Returns metrics including p-values, CIs, and effect sizes.
    """
    pin_random_seed(config.get("RANDOM_SEED", 42))
    
    outcome_col = config.get("outcome_col")
    group_col = config.get("group_col")
    
    # Identify columns if not specified
    if not outcome_col:
        numerical_cols = identify_numerical_columns(df)
        # Assume last numerical column is outcome, second to last is group (or first categorical)
        if len(numerical_cols) >= 2:
            outcome_col = numerical_cols[-1]
            group_col = numerical_cols[-2] if len(numerical_cols) > 1 else None
        elif len(numerical_cols) == 1:
            outcome_col = numerical_cols[0]
            # Try to find a categorical group
            categorical_cols = identify_categorical_columns(df)
            group_col = categorical_cols[0] if categorical_cols else None
    
    if not outcome_col or outcome_col not in df.columns:
        logger.error(f"Outcome column '{outcome_col}' not found in dataset {dataset_name}")
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
    Main entry point for T023: Re-analyze cleaned variants.
    Finds all cleaned datasets, runs analysis, and outputs cleaned_metrics.json.
    """
    logger.info("Starting T023: Re-analyzing cleaned variants")
    
    config = get_config()
    processed_dir = config.get("PROCESSED_DATA_PATH", "data/processed")
    output_file = config.get("CLEANED_METRICS_PATH", "data/processed/cleaned_metrics.json")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Find cleaned datasets
    cleaned_datasets = find_cleaned_datasets(processed_dir)
    
    if not cleaned_datasets:
        logger.warning("No cleaned datasets found. Generating empty report.")
        report = {
            "datasets": [],
            "metadata": {
                "error": "No cleaned datasets found",
                "timestamp": datetime.now().isoformat(),
                "processed_dir": processed_dir
            }
        }
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        return
    
    logger.info(f"Found {len(cleaned_datasets)} cleaned datasets to analyze")
    
    results = []
    for ds in cleaned_datasets:
        try:
            logger.info(f"Processing: {ds['dataset_name']} ({ds['strategy']})")
            df = pd.read_csv(ds['file_path'])
            
            # Validate dataframe
            if df.empty:
                logger.warning(f"Dataset {ds['dataset_name']} is empty, skipping.")
                continue
            
            analysis_result = analyze_cleaned_variant(df, ds['dataset_name'], ds['strategy'], config)
            if analysis_result:
                results.append(analysis_result)
        except Exception as e:
            logger.error(f"Failed to process {ds['dataset_name']}: {e}", exc_info=True)
    
    # Compile final report
    report = {
        "datasets": results,
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "processed_dir": processed_dir,
            "total_datasets_analyzed": len(results),
            "total_datasets_found": len(cleaned_datasets)
        }
    }
    
    # Write output
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Cleaned metrics report saved to {output_file}")
    logger.info(f"Successfully analyzed {len(results)} out of {len(cleaned_datasets)} datasets")

if __name__ == "__main__":
    main()

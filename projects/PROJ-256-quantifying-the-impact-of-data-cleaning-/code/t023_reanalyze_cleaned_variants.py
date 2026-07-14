import os
import sys
import json
import logging
import glob
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

from analysis import run_baseline_analysis, run_t_test, run_linear_regression, compute_effect_size_cohen_d
from utils import setup_logging, compute_file_checksum
from config import get_config

logger = logging.getLogger(__name__)

def find_cleaned_datasets(processed_dir: str) -> List[Dict[str, Any]]:
    """
    Find all cleaned dataset CSVs in the processed directory.
    Returns a list of dicts with 'path', 'dataset_name', 'strategy'.
    """
    pattern = os.path.join(processed_dir, "*_cleaned_*.csv")
    files = glob.glob(pattern)
    
    if not files:
        # Also check for generic cleaned patterns if specific naming varies
        pattern = os.path.join(processed_dir, "*_outlier_removed*.csv")
        files.extend(glob.glob(pattern))
        pattern = os.path.join(processed_dir, "*_imputed*.csv")
        files.extend(glob.glob(pattern))
        pattern = os.path.join(processed_dir, "*_recoded*.csv")
        files.extend(glob.glob(pattern))
    
    # Deduplicate
    files = list(set(files))

    cleaned_datasets = []
    for f in files:
        filename = os.path.basename(f)
        # Infer strategy from filename if possible, else default
        strategy = "unknown"
        if "outlier" in filename:
            strategy = "outlier_removal"
        elif "imputed" in filename:
            strategy = "imputation"
        elif "recoded" in filename:
            strategy = "recoding"
        
        cleaned_datasets.append({
            "path": f,
            "dataset_name": filename.replace(".csv", ""),
            "strategy": strategy
        })
    
    return cleaned_datasets

def analyze_cleaned_variant(
    dataset_path: str,
    dataset_name: str,
    strategy: str,
    outcome_col: str,
    group_col: Optional[str] = None,
    predictors: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Run t-tests and linear regressions on a cleaned dataset variant.
    Returns a dict of metrics suitable for JSON serialization.
    """
    logger.info(f"Analyzing cleaned variant: {dataset_name} (strategy: {strategy})")
    
    if not os.path.exists(dataset_path):
        logger.error(f"Dataset file not found: {dataset_path}")
        return None

    try:
        df = pd.read_csv(dataset_path)
    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_path}: {e}")
        return None

    results = {
        "dataset_name": dataset_name,
        "cleaning_strategy": strategy,
        "checksum": compute_file_checksum(dataset_path),
        "row_count": len(df),
        "column_count": len(df.columns),
        "analysis": {}
    }

    # Identify numerical columns for analysis
    numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if outcome_col and outcome_col in df.columns:
        # Ensure outcome is numerical for regression
        if not np.issubdtype(df[outcome_col].dtype, np.number):
            logger.warning(f"Outcome column {outcome_col} is not numerical. Skipping regression.")
        else:
            # Run Linear Regression
            # We need at least one predictor. If not provided, try to find one.
            potential_predictors = [c for c in numerical_cols if c != outcome_col]
            
            if predictors:
                valid_predictors = [p for p in predictors if p in df.columns]
            elif potential_predictors:
                valid_predictors = [potential_predictors[0]] # Take first available
            else:
                valid_predictors = []

            if valid_predictors:
                try:
                    reg_result = run_linear_regression(df, outcome_col, valid_predictors)
                    results["analysis"]["regression"] = {
                        "predictors": valid_predictors,
                        "r_squared": float(reg_result['r_squared']) if 'r_squared' in reg_result else None,
                        "p_values": [float(p) for p in reg_result.get('p_values', [])],
                        "coefficients": [float(c) for c in reg_result.get('coefficients', [])]
                    }
                except Exception as e:
                    logger.warning(f"Regression failed for {dataset_name}: {e}")
                    results["analysis"]["regression"] = {"error": str(e)}

        # Run T-Test if group_col is provided
        if group_col and group_col in df.columns:
            try:
                # Ensure group column has at least 2 unique values
                unique_groups = df[group_col].nunique()
                if unique_groups >= 2:
                    # Take first two unique groups for t-test
                    groups = df[group_col].unique()[:2]
                    t_res = run_t_test(df, outcome_col, group_col, groups[0], groups[1])
                    results["analysis"]["t_test"] = {
                        "group_col": group_col,
                        "groups": [str(groups[0]), str(groups[1])],
                        "p_value": float(t_res['p_value']),
                        "t_statistic": float(t_res['t_statistic']),
                        "ci_lower": float(t_res['ci_lower']),
                        "ci_upper": float(t_res['ci_upper']),
                        "effect_size_cohen_d": float(t_res.get('effect_size_cohen_d', 0))
                    }
                else:
                    logger.warning(f"Not enough groups for t-test in {dataset_name}")
            except Exception as e:
                logger.warning(f"T-test failed for {dataset_name}: {e}")
                results["analysis"]["t_test"] = {"error": str(e)}
    else:
        logger.warning(f"Outcome column {outcome_col} not found in {dataset_name}")

    return results

def main():
    """
    Main entry point for T023: Re-run t-tests and linear regressions on each cleaned variant.
    Output: data/processed/cleaned_metrics.json
    """
    setup_logging("INFO")
    config = get_config()

    processed_dir = config.get("PROCESSED_DATA_PATH", "data/processed")
    outcome_col = config.get("outcome_col", "outcome") # Default or from config
    group_col = config.get("group_col", None) # Optional
    predictors = config.get("predictors", None) # Optional list

    output_file = config.get("CLEANED_METRICS_PATH", "data/processed/cleaned_metrics.json")

    logger.info(f"Scanning for cleaned datasets in {processed_dir}")
    cleaned_datasets = find_cleaned_datasets(processed_dir)

    if not cleaned_datasets:
        logger.error("No cleaned datasets found. Ensure cleaning strategies have been applied (T022).")
        sys.exit(1)

    logger.info(f"Found {len(cleaned_datasets)} cleaned dataset variants.")

    all_metrics = []
    success_count = 0

    for ds_info in cleaned_datasets:
        metrics = analyze_cleaned_variant(
            dataset_path=ds_info["path"],
            dataset_name=ds_info["dataset_name"],
            strategy=ds_info["strategy"],
            outcome_col=outcome_col,
            group_col=group_col,
            predictors=predictors
        )
        
        if metrics:
            all_metrics.append(metrics)
            success_count += 1
            logger.info(f"Successfully analyzed {ds_info['dataset_name']}")
        else:
            logger.warning(f"Skipped analysis for {ds_info['dataset_name']} due to errors")

    if success_count == 0:
        logger.error("Failed to analyze any cleaned datasets.")
        sys.exit(1)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Write results to JSON
    with open(output_file, 'w') as f:
        json.dump(all_metrics, f, indent=2)

    logger.info(f"Cleaned metrics written to {output_file}")
    logger.info(f"Total datasets analyzed: {success_count}/{len(cleaned_datasets)}")

    return 0

if __name__ == "__main__":
    sys.exit(main())

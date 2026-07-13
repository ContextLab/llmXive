import os
import sys
import json
import logging
import glob
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np

# Import from existing project modules
from analysis import run_t_test, run_linear_regression, compute_effect_size_cohen_d
from config import Config, get_config
from utils import pin_random_seed, setup_logging

logger = logging.getLogger(__name__)

def find_cleaned_datasets(processed_dir: str) -> List[Dict[str, str]]:
    """
    Find all cleaned dataset CSVs in the processed directory.
    Expects naming convention: <dataset_name>_<strategy>.csv
    Returns a list of dicts with 'path', 'dataset_name', 'strategy'.
    """
    cleaned_files = glob.glob(os.path.join(processed_dir, "*_*.csv"))
    # Filter out files that don't match the expected pattern (e.g., baseline_metrics.json)
    # We expect CSVs.
    
    results = []
    for f in cleaned_files:
        basename = os.path.basename(f)
        if not basename.endswith('.csv'):
            continue
        
        # Parse name: assume format "datasetname_strategy.csv"
        # Split by last underscore
        parts = basename.rsplit('_', 1)
        if len(parts) != 2:
            logger.warning(f"Skipping file with unexpected naming convention: {basename}")
            continue
        
        dataset_name = parts[0]
        strategy = parts[1].replace('.csv', '')
        
        # Skip if strategy looks like a metric file name or invalid
        if strategy in ['metrics', 'baseline', 'null']:
            continue

        results.append({
            'path': f,
            'dataset_name': dataset_name,
            'strategy': strategy
        })
    
    return results

def extract_strategy_from_filename(filename: str) -> str:
    """Extract strategy name from filename like 'har_iqr.csv'."""
    basename = os.path.basename(filename)
    name_part = basename.rsplit('.', 1)[0]
    if '_' in name_part:
        return name_part.rsplit('_', 1)[1]
    return "unknown"

def analyze_cleaned_variant(
    df: pd.DataFrame, 
    dataset_name: str, 
    strategy: str, 
    config: Config
) -> Optional[Dict[str, Any]]:
    """
    Run t-tests and linear regressions on a cleaned dataset variant.
    Returns a dictionary of metrics.
    """
    pin_random_seed(config.get("RANDOM_SEED", 42))
    
    if df.empty:
        logger.warning(f"Dataset {dataset_name} ({strategy}) is empty after cleaning.")
        return None

    # Identify numeric columns for analysis
    # We assume the last column is the target/outcome for simplicity, 
    # or we look for a column named 'target'/'outcome' if present.
    # Based on previous tasks (T012), we likely need to infer columns.
    # Let's assume standard structure: predictors are all numeric except the last one (target).
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if len(numeric_cols) < 2:
        logger.warning(f"Not enough numeric columns in {dataset_name} ({strategy}) to run analysis.")
        return None

    # Heuristic: Last numeric column is target, rest are predictors
    # This matches the pattern in T012 usually.
    target_col = numeric_cols[-1]
    predictor_cols = numeric_cols[:-1]

    results = {
        "dataset_name": dataset_name,
        "strategy": strategy,
        "n_rows": len(df),
        "n_cols": len(df.columns),
        "t_test": None,
        "regression": None
    }

    # Run T-Test: Compare target against a binary split of the first predictor?
    # Or compare two groups if a categorical split exists.
    # Since we need to match T012 baseline logic, let's assume:
    # 1. T-test: Compare target means across the median split of the first predictor.
    # 2. Regression: Target ~ all other predictors.
    
    if len(predictor_cols) > 0:
        predictor = predictor_cols[0]
        median_val = df[predictor].median()
        group_0 = df[df[predictor] <= median_val][target_col]
        group_1 = df[df[predictor] > median_val][target_col]

        if len(group_0) > 1 and len(group_1) > 1:
            try:
                t_stat, p_val = run_t_test(group_0, group_1)
                # Calculate Cohen's d
                mean_diff = group_1.mean() - group_0.mean()
                pooled_std = np.sqrt((group_0.std()**2 + group_1.std()**2) / 2)
                cohens_d = mean_diff / pooled_std if pooled_std != 0 else 0.0
                
                results["t_test"] = {
                    "p_value": float(p_val),
                    "t_statistic": float(t_stat),
                    "effect_size_cohen_d": float(cohens_d),
                    "group_0_n": len(group_0),
                    "group_1_n": len(group_1)
                }
            except Exception as e:
                logger.error(f"Failed t-test on {dataset_name}: {e}")

    # Run Linear Regression
    if len(predictor_cols) > 0:
        try:
            X = df[predictor_cols]
            y = df[target_col]
            
            # Filter out rows with NaN in predictors or target
            mask = ~(X.isna().any(axis=1) | y.isna())
            X_clean = X[mask]
            y_clean = y[mask]
            
            if len(X_clean) < 2:
                logger.warning("Not enough data points for regression after NaN removal.")
            else:
                reg_result = run_linear_regression(X_clean, y_clean)
                
                results["regression"] = {
                    "coefficients": [float(c) for c in reg_result.get("coefficients", [])],
                    "p_values": [float(p) for p in reg_result.get("p_values", [])],
                    "r_squared": float(reg_result.get("r_squared", 0)),
                    "adj_r_squared": float(reg_result.get("adj_r_squared", 0)),
                    "n_samples": len(X_clean)
                }
        except Exception as e:
            logger.error(f"Failed regression on {dataset_name}: {e}")

    return results

def main():
    """
    Main entry point for T023: Re-run analysis on cleaned variants.
    Reads cleaned CSVs from data/processed/, runs analysis, saves to cleaned_metrics.json.
    """
    setup_logging("INFO")
    
    # Load config
    config = get_config()
    
    # Paths
    processed_dir = config.get("PROCESSED_DATA_PATH", "data/processed")
    output_file = os.path.join(processed_dir, "cleaned_metrics.json")
    
    logger.info(f"Scanning for cleaned datasets in {processed_dir}")
    cleaned_datasets = find_cleaned_datasets(processed_dir)
    
    if not cleaned_datasets:
        logger.warning("No cleaned datasets found. Ensure T022 has run successfully.")
        # Create an empty report to satisfy the output requirement
        empty_report = {
            "metadata": {
                "generated_at": str(pd.Timestamp.now()),
                "script": "t023_reanalyze_cleaned_variants.py",
                "source": "T023"
            },
            "datasets": [],
            "summary": {
                "total_analyzed": 0,
                "strategies_found": []
            }
        }
        with open(output_file, 'w') as f:
            json.dump(empty_report, f, indent=2)
        logger.info(f"Wrote empty report to {output_file}")
        return

    logger.info(f"Found {len(cleaned_datasets)} cleaned datasets.")
    
    all_results = []
    strategies_found = set()
    
    for item in cleaned_datasets:
        logger.info(f"Analyzing: {item['dataset_name']} ({item['strategy']})")
        try:
            df = pd.read_csv(item['path'])
            result = analyze_cleaned_variant(df, item['dataset_name'], item['strategy'], config)
            if result:
                all_results.append(result)
                strategies_found.add(item['strategy'])
        except Exception as e:
            logger.error(f"Error processing {item['path']}: {e}", exc_info=True)
    
    # Compile report
    report = {
        "metadata": {
            "generated_at": str(pd.Timestamp.now()),
            "script": "t023_reanalyze_cleaned_variants.py",
            "source": "T023"
        },
        "datasets": all_results,
        "summary": {
            "total_analyzed": len(all_results),
            "strategies_found": list(strategies_found)
        }
    }
    
    # Write output
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Successfully wrote cleaned metrics to {output_file}")

if __name__ == "__main__":
    main()
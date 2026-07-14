"""
T032: Implement permutation null dataset generation for FPR estimation.

Generates null datasets by shuffling the outcome variable while keeping predictors fixed.
Runs baseline analysis on these null datasets to estimate the False Positive Rate (FPR).
Outputs: data/processed/null_fpr_metrics.json
"""
import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime

# Project imports
from utils import setup_logging, pin_random_seed
from config import Config, get_config
from analysis import run_baseline_analysis, load_datasets_from_raw

logger = logging.getLogger(__name__)

def load_baseline_metrics(filepath: str = None) -> Dict[str, Any]:
    """
    Load baseline metrics from the processed directory.
    Fallbacks to default path if not provided.
    """
    if filepath is None:
        config = get_config()
        filepath = os.path.join(config.get("PROCESSED_DATA_PATH", "data/processed"), "baseline_metrics.json")
    
    if not os.path.exists(filepath):
        logger.error(f"Baseline metrics file not found: {filepath}")
        return {}
    
    with open(filepath, 'r') as f:
        return json.load(f)

def load_dataset_from_processed(dataset_name: str, processed_dir: str = None) -> Optional[pd.DataFrame]:
    """
    Load a specific dataset from the processed directory.
    """
    if processed_dir is None:
        config = get_config()
        processed_dir = config.get("PROCESSED_DATA_PATH", "data/processed")
    
    # Try to find the file
    # Assuming naming convention: {dataset_name}.csv or similar
    # We might need to scan the directory if the exact filename isn't known
    # For now, we assume the dataset_name matches the base filename without extension
    candidates = [
        os.path.join(processed_dir, f"{dataset_name}.csv"),
        os.path.join(processed_dir, f"{dataset_name}_cleaned.csv"),
        os.path.join(processed_dir, f"{dataset_name}_outlier_removed.csv"),
    ]
    
    for candidate in candidates:
        if os.path.exists(candidate):
            logger.info(f"Loading dataset from: {candidate}")
            return pd.read_csv(candidate)
    
    # Fallback: try to load from raw if processed doesn't have it
    # This handles cases where the dataset was never cleaned but exists in raw
    raw_dir = config.get("RAW_DATA_PATH", "data/raw")
    raw_candidates = [
        os.path.join(raw_dir, f"{dataset_name}.csv"),
        os.path.join(raw_dir, f"{dataset_name}.xlsx"), # Handle Excel files if necessary
    ]
    
    for candidate in raw_candidates:
        if os.path.exists(candidate):
            logger.info(f"Loading dataset from raw: {candidate}")
            if candidate.endswith('.xlsx'):
                return pd.read_excel(candidate)
            return pd.read_csv(candidate)
    
    logger.warning(f"Could not find dataset for permutation: {dataset_name}")
    return None

def generate_null_dataset(df: pd.DataFrame, outcome_col: str, seed: int = None) -> pd.DataFrame:
    """
    Generate a null dataset by shuffling the outcome variable.
    Predictors remain fixed; outcome is permuted to break any true relationship.
    """
    if seed is not None:
        pin_random_seed(seed)
    
    df_null = df.copy()
    
    if outcome_col not in df_null.columns:
        logger.error(f"Outcome column '{outcome_col}' not found in dataset.")
        return None
    
    # Shuffle the outcome column
    shuffled_outcome = df_null[outcome_col].sample(frac=1, random_state=seed).reset_index(drop=True)
    df_null[outcome_col] = shuffled_outcome
    
    logger.info(f"Generated null dataset by shuffling '{outcome_col}'")
    return df_null

def estimate_fpr_for_dataset(
    df_null: pd.DataFrame, 
    dataset_name: str, 
    outcome_col: str, 
    config: Config,
    seed: int = None
) -> Dict[str, Any]:
    """
    Run analysis on a null dataset and estimate FPR.
    FPR is the proportion of tests that yield p <= 0.05 (false positives).
    """
    if seed is not None:
        pin_random_seed(seed)
    
    logger.info(f"Running analysis on null dataset for: {dataset_name}")
    
    # Run baseline analysis on the null dataset
    # We pass df directly, expecting run_baseline_analysis to handle it
    # Based on API surface: run_baseline_analysis(df, dataset_name=dataset_name, config=config)
    try:
        results = run_baseline_analysis(df_null, dataset_name=dataset_name, config=config)
    except Exception as e:
        logger.error(f"Failed to analyze null dataset for {dataset_name}: {e}")
        return {
            "dataset_name": dataset_name,
            "status": "error",
            "error": str(e),
            "fpr": None,
            "num_tests": 0,
            "num_significant": 0
        }
    
    if not results or not results.get('success', False):
        logger.warning(f"Analysis failed for null dataset: {dataset_name}")
        return {
            "dataset_name": dataset_name,
            "status": "failed",
            "fpr": None,
            "num_tests": 0,
            "num_significant": 0
        }
    
    # Extract results
    # The structure of 'results' depends on run_baseline_analysis output.
    # Assuming it returns a dict with 't_test' and 'regression' keys or similar.
    # We need to count how many tests had p <= 0.05.
    
    num_tests = 0
    num_significant = 0
    significant_tests = []
    
    # Handle potential structure variations
    tests_data = results.get('t_test', {})
    if tests_data:
        if isinstance(tests_data, dict):
            for test_name, test_res in tests_data.items():
                num_tests += 1
                p_val = test_res.get('p_value')
                if p_val is not None and p_val <= 0.05:
                    num_significant += 1
                    significant_tests.append({"test": test_name, "p_value": p_val})
        elif isinstance(tests_data, list):
            for test_res in tests_data:
                num_tests += 1
                p_val = test_res.get('p_value')
                if p_val is not None and p_val <= 0.05:
                    num_significant += 1
                    significant_tests.append({"test": "t_test", "p_value": p_val})
    
    # Check regression results if present
    reg_data = results.get('regression', {})
    if reg_data:
        if isinstance(reg_data, dict):
            for model_name, model_res in reg_data.items():
                num_tests += 1
                p_val = model_res.get('p_value') # Assuming p_value is top level or in coefficients
                # If p_value is in coefficients list, we might need to check multiple
                if p_val is None and 'coefficients' in model_res:
                    # Check coefficients for significance
                    coeffs = model_res['coefficients']
                    if isinstance(coeffs, list):
                        for c in coeffs:
                            if c.get('p_value', 1.0) <= 0.05:
                                num_significant += 1
                                break # Count as one significant regression test
                elif p_val is not None and p_val <= 0.05:
                    num_significant += 1
                    significant_tests.append({"test": model_name, "p_value": p_val})
    
    fpr = num_significant / num_tests if num_tests > 0 else 0.0
    
    return {
        "dataset_name": dataset_name,
        "status": "success",
        "fpr": fpr,
        "num_tests": num_tests,
        "num_significant": num_significant,
        "significant_tests": significant_tests
    }

def write_output(metrics: List[Dict[str, Any]], output_path: str):
    """
    Write the FPR metrics to a JSON file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    output_data = {
        "generated_at": datetime.now().isoformat(),
        "description": "False Positive Rate (FPR) estimation using permutation null datasets",
        "metrics": metrics,
        "summary": {
            "total_datasets": len(metrics),
            "successful_datasets": sum(1 for m in metrics if m.get('status') == 'success'),
            "average_fpr": np.mean([m['fpr'] for m in metrics if m.get('fpr') is not None]) if any(m.get('fpr') is not None for m in metrics) else None
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Wrote FPR metrics to {output_path}")

def main():
    """
    Main entry point for T032.
    """
    setup_logging("INFO")
    config = get_config()
    
    seed = config.get("RANDOM_SEED", 42)
    pin_random_seed(seed)
    
    processed_dir = config.get("PROCESSED_DATA_PATH", "data/processed")
    output_path = os.path.join(processed_dir, "null_fpr_metrics.json")
    
    logger.info("Starting T032: Permutation Null FPR Estimation")
    
    # Load baseline metrics to get list of datasets
    baseline_metrics = load_baseline_metrics()
    
    if not baseline_metrics:
        logger.error("No baseline metrics found. Cannot proceed with FPR estimation.")
        sys.exit(1)
    
    datasets = baseline_metrics.get("datasets", [])
    if not datasets:
        # Fallback: try to load from the structure if 'datasets' key is missing
        # Sometimes baseline_metrics might be a list directly or have different structure
        if isinstance(baseline_metrics, list):
            datasets = baseline_metrics
        else:
            # Try to infer from keys if it's a dict of datasets
            datasets = [{"dataset_name": k} for k in baseline_metrics.keys() if k != "generated_at"]
    
    if not datasets:
        logger.error("No datasets found in baseline metrics.")
        sys.exit(1)
    
    logger.info(f"Found {len(datasets)} datasets to process for FPR estimation.")
    
    fpr_results = []
    
    for entry in datasets:
        dataset_name = entry.get("dataset_name")
        if not dataset_name:
            # Try alternative keys
            dataset_name = entry.get("name") or entry.get("id")
        
        if not dataset_name:
            logger.warning("Skipping entry without dataset name.")
            continue
        
        logger.info(f"Processing null dataset for: {dataset_name}")
        
        # Load original dataset
        df = load_dataset_from_processed(dataset_name, processed_dir)
        if df is None:
            logger.warning(f"Could not load original dataset for {dataset_name}, skipping.")
            fpr_results.append({
                "dataset_name": dataset_name,
                "status": "skipped",
                "reason": "Dataset not found"
            })
            continue
        
        # Determine outcome column
        # We need to know which column is the outcome. 
        # This is often specified in the baseline metrics or config.
        # If not specified, we might need to infer or skip.
        outcome_col = entry.get("outcome_column")
        
        if not outcome_col:
            # Try to infer from common names or config
            outcome_col = config.get("OUTCOME_COLUMN")
            if not outcome_col:
                # Last resort: look for a column that looks like an outcome
                # This is risky, but we need something to run.
                # For now, we'll skip if we can't find it.
                logger.warning(f"No outcome column specified for {dataset_name}, skipping.")
                fpr_results.append({
                    "dataset_name": dataset_name,
                    "status": "skipped",
                    "reason": "Outcome column not specified"
                })
                continue
        
        if outcome_col not in df.columns:
            logger.warning(f"Outcome column '{outcome_col}' not in dataset columns: {list(df.columns)}. Skipping.")
            fpr_results.append({
                "dataset_name": dataset_name,
                "status": "skipped",
                "reason": f"Outcome column '{outcome_col}' not found"
            })
            continue
        
        # Generate null dataset
        df_null = generate_null_dataset(df, outcome_col, seed=seed)
        if df_null is None:
            logger.error(f"Failed to generate null dataset for {dataset_name}")
            continue
        
        # Estimate FPR
        result = estimate_fpr_for_dataset(df_null, dataset_name, outcome_col, config, seed=seed)
        fpr_results.append(result)
        
        # Increment seed for next permutation to ensure independence
        seed += 1
    
    # Write output
    write_output(fpr_results, output_path)
    
    logger.info("T032 completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())

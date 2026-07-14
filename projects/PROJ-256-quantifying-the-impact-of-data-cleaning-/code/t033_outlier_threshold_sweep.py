"""
Task T033: Implement outlier threshold sweep for k values.

Calculates False Positive Rate (FPR) and Inconsistency Rate per threshold k.
Dependencies: cleaning functions (T017-T021), analysis functions (T012, T023).
"""
import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# Import from project modules
from utils import setup_logging, pin_random_seed
from config import Config
from cleaning import apply_iqr_outlier_removal
from analysis import run_baseline_analysis
from reporting import load_json_file

# Configure logger
logger = setup_logging("INFO")

# Thresholds to sweep
THRESHOLDS = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]

def load_baseline_metrics(filepath: str) -> Dict[str, Any]:
    """Load baseline metrics from JSON file."""
    return load_json_file(filepath)

def load_cleaned_metrics(filepath: str) -> Dict[str, Any]:
    """Load cleaned metrics from JSON file."""
    return load_json_file(filepath)

def load_dataset_from_processed(dataset_name: str, processed_dir: str) -> pd.DataFrame:
    """Load a specific dataset from the processed directory."""
    # Handle both .csv and .csv.gz
    path_csv = os.path.join(processed_dir, f"{dataset_name}.csv")
    path_gz = os.path.join(processed_dir, f"{dataset_name}.csv.gz")
    
    if os.path.exists(path_csv):
        return pd.read_csv(path_csv)
    elif os.path.exists(path_gz):
        return pd.read_csv(path_gz)
    else:
        # Try to find file with strategy suffix if exact name not found
        # This is a fallback for naming variations
        for f in os.listdir(processed_dir):
            if f.startswith(dataset_name):
                full_path = os.path.join(processed_dir, f)
                logger.info(f"Found variant: {f} for {dataset_name}")
                if f.endswith('.gz'):
                    return pd.read_csv(full_path)
                return pd.read_csv(full_path)
        
        raise FileNotFoundError(f"Could not find dataset {dataset_name} in {processed_dir}")

def estimate_fpr_for_dataset(
    df: pd.DataFrame, 
    outcome_col: str, 
    predictor_cols: List[str],
    k: float,
    config: Config
) -> float:
    """
    Estimate False Positive Rate for a specific dataset and threshold k.
    
    1. Generate null datasets by shuffling the outcome variable.
    2. Apply outlier removal with threshold k.
    3. Run statistical tests on the cleaned null data.
    4. Calculate FPR as proportion of tests with p <= 0.05.
    """
    pin_random_seed(config.get("RANDOM_SEED", 42))
    
    num_permutations = 100  # Reduced for performance in sweep
    significant_count = 0
    
    for i in range(num_permutations):
        # Create null dataset by shuffling outcome
        df_null = df.copy()
        df_null[outcome_col] = np.random.permutation(df_null[outcome_col].values)
        
        # Apply outlier removal
        try:
            df_clean = apply_iqr_outlier_removal(df_null, k=k)
        except Exception as e:
            logger.warning(f"Cleaning failed for permutation {i}: {e}")
            continue
        
        # Run analysis on cleaned null data
        # We need to identify columns again
        from analysis import identify_numerical_columns
        num_cols = identify_numerical_columns(df_clean)
        
        # Filter to predictor_cols and outcome_col if they exist in num_cols
        valid_predictors = [c for c in predictor_cols if c in num_cols]
        
        if not valid_predictors or outcome_col not in num_cols:
            continue
        
        # Run t-test or regression on null data
        # For simplicity, we run t-tests between outcome and each predictor
        # (Assuming binary outcome or similar for t-test, otherwise regression)
        # We'll use a simple correlation-based significance check or t-test
        
        # Using t-test if outcome is binary-like, else regression
        # For general robustness, let's run a simple linear regression F-test
        # or t-test depending on data shape.
        
        # Simple approach: run t-test for each predictor against outcome
        # If outcome is continuous, we might need correlation. 
        # Let's assume we are testing for difference in means or correlation.
        # To be safe, we'll use scipy.stats for t-test if binary, else pearsonr
        from scipy import stats
        
        p_values = []
        for pred in valid_predictors:
            try:
                if df_clean[outcome_col].nunique() == 2:
                    # T-test
                    group0 = df_clean[df_clean[outcome_col] == df_clean[outcome_col].unique()[0]][pred]
                    group1 = df_clean[df_clean[outcome_col] == df_clean[outcome_col].unique()[1]][pred]
                    _, p_val = stats.ttest_ind(group0, group1)
                else:
                    # Correlation
                    _, p_val = stats.pearsonr(df_clean[outcome_col], df_clean[pred])
                
                if not np.isnan(p_val):
                    p_values.append(p_val)
            except Exception:
                continue
        
        if p_values:
            # Check if ANY test is significant (standard for FPR in multiple testing context)
            # Or check proportion. Here we count if ANY null hypothesis is rejected.
            if any(p <= 0.05 for p in p_values):
                significant_count += 1
    
    if num_permutations == 0:
        return 0.0
    return significant_count / num_permutations

def calculate_inconsistency_rate(
    baseline_metrics: Dict[str, Any],
    cleaned_metrics: Dict[str, Any],
    k: float,
    strategy_name: str = "outlier_removed"
) -> float:
    """
    Calculate Inconsistency Rate: proportion of datasets where significance status changes.
    
    Compares baseline p-value (sig if p <= 0.05) vs cleaned p-value (sig if p <= 0.05).
    """
    if not baseline_metrics.get('datasets') or not cleaned_metrics.get('datasets'):
        logger.warning("Missing datasets in metrics for inconsistency calculation.")
        return 0.0
    
    baseline_list = baseline_metrics['datasets']
    cleaned_list = cleaned_metrics['datasets']
    
    # Map cleaned datasets by name
    cleaned_map = {d['dataset_name']: d for d in cleaned_list}
    
    inconsistency_count = 0
    total_count = 0
    
    for b_entry in baseline_list:
        d_name = b_entry['dataset_name']
        if d_name not in cleaned_map:
            # Check for suffix
            found = False
            for c_name in cleaned_map:
                if d_name in c_name:
                    cleaned_map[d_name] = cleaned_map[c_name]
                    found = True
                    break
            if not found:
                continue
        
        c_entry = cleaned_map[d_name]
        
        # Extract p-values (assuming t-test or regression F-stat p-value)
        # Structure: b_entry['analysis']['t_test']['p_value'] or similar
        # We need a robust way to get the primary p-value
        
        def get_p_value(entry):
            if 'analysis' in entry:
                if 't_test' in entry['analysis']:
                    return entry['analysis']['t_test'].get('p_value')
                if 'regression' in entry['analysis']:
                    return entry['analysis']['regression'].get('p_value')
            return None
        
        p_base = get_p_value(b_entry)
        p_clean = get_p_value(c_entry)
        
        if p_base is None or p_clean is None:
            continue
        
        sig_base = p_base <= 0.05
        sig_clean = p_clean <= 0.05
        
        if sig_base != sig_clean:
            inconsistency_count += 1
        
        total_count += 1
    
    if total_count == 0:
        return 0.0
    return inconsistency_count / total_count

def run_threshold_sweep(
    config: Config,
    baseline_metrics: Dict[str, Any],
    cleaned_metrics: Dict[str, Any],
    processed_dir: str
) -> List[Dict[str, Any]]:
    """
    Run the threshold sweep for k in THRESHOLDS.
    Returns a list of results for each k.
    """
    results = []
    
    # Identify datasets to process
    # We need the original raw datasets to generate nulls
    # We'll use the dataset names from baseline metrics
    dataset_names = [d['dataset_name'] for d in baseline_metrics.get('datasets', [])]
    
    logger.info(f"Starting threshold sweep for {len(THRESHOLDS)} thresholds on {len(dataset_names)} datasets.")
    
    for k in THRESHOLDS:
        logger.info(f"Processing threshold k={k}")
        
        fpr_values = []
        inconsistency_rates = []
        
        for d_name in dataset_names:
            try:
                # Load raw dataset (from processed dir if that's where we have them, 
                # but ideally raw. We assume processed dir has the CSVs available)
                # Note: T032 generated nulls, but we need to re-generate for specific k
                # We need the original data. Let's assume we load from processed_dir 
                # where the original CSVs might be stored or re-download.
                # For this implementation, we assume the 'cleaned' datasets in processed_dir
                # are derived from the raw ones, but we need the RAW for null generation.
                # If raw is not in processed_dir, we might need to look in raw_dir.
                
                # Let's try to load from processed_dir first (as T011/T012 might have put them there)
                # or raw_dir if available.
                raw_dir = config.get("RAW_DATA_PATH", "data/raw")
                processed_dir_path = config.get("PROCESSED_DATA_PATH", "data/processed")
                
                # Try raw first
                df = None
                if os.path.exists(raw_dir):
                    try:
                        df = load_dataset_from_processed(d_name, raw_dir)
                    except FileNotFoundError:
                        pass
                
                if df is None:
                    # Try processed
                    df = load_dataset_from_processed(d_name, processed_dir_path)
                
                if df is None:
                    logger.warning(f"Could not load dataset {d_name} for FPR estimation.")
                    continue
                
                # Identify outcome and predictors
                # We need to know which column is outcome. 
                # Let's assume the last column is outcome or use metadata if available.
                # For robustness, we'll try to infer or use a standard convention.
                # If metadata exists in the dataset, use it. Otherwise, assume last column.
                columns = df.columns.tolist()
                outcome_col = columns[-1] # Heuristic
                predictor_cols = columns[:-1]
                
                # Estimate FPR
                fpr = estimate_fpr_for_dataset(df, outcome_col, predictor_cols, k, config)
                fpr_values.append(fpr)
                
                # Calculate Inconsistency Rate
                irr = calculate_inconsistency_rate(baseline_metrics, cleaned_metrics, k)
                inconsistency_rates.append(irr)
                
            except Exception as e:
                logger.error(f"Error processing dataset {d_name} at k={k}: {e}")
                continue
        
        # Aggregate results for this k
        avg_fpr = np.mean(fpr_values) if fpr_values else 0.0
        avg_irr = np.mean(inconsistency_rates) if inconsistency_rates else 0.0
        
        results.append({
            "threshold_k": k,
            "average_fpr": avg_fpr,
            "average_inconsistency_rate": avg_irr,
            "datasets_processed": len(fpr_values)
        })
    
    return results

def write_output(results: List[Dict[str, Any]], output_path: str):
    """Write the sweep results to a JSON file."""
    output_data = {
        "timestamp": datetime.now().isoformat(),
        "thresholds_tested": THRESHOLDS,
        "results": results
    }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Threshold sweep results written to {output_path}")

def main():
    """Main entry point for T033."""
    logger.info("Starting T033: Outlier Threshold Sweep")
    
    config = Config()
    pin_random_seed(config.get("RANDOM_SEED", 42))
    
    # Load metrics
    baseline_path = os.path.join(config.get("PROCESSED_DATA_PATH", "data/processed"), "baseline_metrics.json")
    cleaned_path = os.path.join(config.get("PROCESSED_DATA_PATH", "data/processed"), "cleaned_metrics.json")
    
    if not os.path.exists(baseline_path):
        logger.error(f"Baseline metrics not found at {baseline_path}. Run T012 first.")
        sys.exit(1)
    
    if not os.path.exists(cleaned_path):
        logger.error(f"Cleaned metrics not found at {cleaned_path}. Run T023 first.")
        sys.exit(1)
    
    baseline_metrics = load_baseline_metrics(baseline_path)
    cleaned_metrics = load_cleaned_metrics(cleaned_path)
    
    processed_dir = config.get("PROCESSED_DATA_PATH", "data/processed")
    
    # Run sweep
    results = run_threshold_sweep(config, baseline_metrics, cleaned_metrics, processed_dir)
    
    # Write output
    output_path = os.path.join(processed_dir, "outlier_threshold_sweep.json")
    write_output(results, output_path)
    
    logger.info("T033 completed successfully.")

if __name__ == "__main__":
    main()

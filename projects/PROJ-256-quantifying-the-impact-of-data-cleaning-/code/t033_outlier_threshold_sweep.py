import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from utils import setup_logging, pin_random_seed
from config import get_config
from analysis import run_baseline_analysis, load_datasets_from_raw
from cleaning import apply_iqr_outlier_removal

logger = logging.getLogger(__name__)

def load_baseline_metrics(filepath: str) -> Dict[str, Any]:
    """Load baseline metrics from JSON."""
    if not os.path.exists(filepath):
        logger.error(f"Baseline metrics file not found: {filepath}")
        return {}
    with open(filepath, 'r') as f:
        return json.load(f)

def load_cleaned_metrics(filepath: str) -> Dict[str, Any]:
    """Load cleaned metrics from JSON."""
    if not os.path.exists(filepath):
        logger.error(f"Cleaned metrics file not found: {filepath}")
        return {}
    with open(filepath, 'r') as f:
        return json.load(f)

def load_dataset_from_processed(filepath: str) -> pd.DataFrame:
    """Load a dataset from the processed directory."""
    return pd.read_csv(filepath)

def generate_null_dataset(df: pd.DataFrame, seed: int) -> pd.DataFrame:
    """Generate a null dataset by shuffling the outcome column."""
    pin_random_seed(seed)
    df_null = df.copy()
    numeric_cols = df_null.select_dtypes(include=[np.number]).columns.tolist()
    if len(numeric_cols) < 1:
        return df_null
    
    outcome_col = numeric_cols[-1]
    df_null[outcome_col] = np.random.permutation(df_null[outcome_col].values)
    return df_null

def estimate_fpr_for_dataset(df_null: pd.DataFrame, threshold_k: float) -> float:
    """
    Estimate False Positive Rate (FPR) for a null dataset at a given outlier threshold k.
    FPR = proportion of tests with p <= 0.05.
    """
    # Apply outlier removal with threshold k
    # Note: apply_iqr_outlier_removal expects k as the multiplier for IQR
    df_cleaned = apply_iqr_outlier_removal(df_null, k=threshold_k)
    
    if len(df_cleaned) == 0:
        logger.warning("Dataset empty after outlier removal.")
        return 0.0
    
    # Run analysis on the cleaned null dataset
    # We treat this as a single dataset analysis
    results = run_baseline_analysis(df_cleaned, dataset_name=f"null_k_{threshold_k}")
    
    if not results:
        return 0.0
    
    total_tests = 0
    significant_tests = 0
    
    # Check t-tests
    for pred, res in results.get("t_tests", {}).items():
        if res.get("p_value") is not None:
            total_tests += 1
            if res["p_value"] <= 0.05:
                significant_tests += 1
    
    # Check regressions
    for pred, res in results.get("regressions", {}).items():
        if res.get("p_value") is not None:
            total_tests += 1
            if res["p_value"] <= 0.05:
                significant_tests += 1
    
    if total_tests == 0:
        return 0.0
    
    fpr = significant_tests / total_tests
    return fpr

def calculate_inconsistency_rate(
    baseline_results: List[Dict], 
    cleaned_results: List[Dict],
    threshold_k: float
) -> float:
    """
    Calculate Inconsistency Rate: proportion of datasets where significance status changes.
    """
    if not baseline_results or not cleaned_results:
        return 0.0
    
    if len(baseline_results) != len(cleaned_results):
        logger.warning("Mismatch in number of datasets between baseline and cleaned.")
        return 0.0
    
    inconsistencies = 0
    total_comparisons = 0
    
    for b_entry, c_entry in zip(baseline_results, cleaned_results):
        b_name = b_entry.get("dataset_name")
        c_name = c_entry.get("dataset_name")
        
        if b_name != c_name:
            logger.warning(f"Dataset name mismatch: {b_name} vs {c_name}")
            continue
        
        # Compare significance status across all tests
        b_tests = b_entry.get("t_tests", {})
        c_tests = c_entry.get("t_tests", {})
        b_regs = b_entry.get("regressions", {})
        c_regs = c_entry.get("regressions", {})
        
        all_preds = set(list(b_tests.keys()) + list(b_regs.keys()))
        
        for pred in all_preds:
            b_sig = False
            c_sig = False
            
            # T-test
            if pred in b_tests and b_tests[pred].get("p_value") is not None:
                total_comparisons += 1
                if b_tests[pred]["p_value"] <= 0.05:
                    b_sig = True
                if pred in c_tests and c_tests[pred].get("p_value") is not None:
                    if c_tests[pred]["p_value"] <= 0.05:
                        c_sig = True
                if b_sig != c_sig:
                    inconsistencies += 1
            
            # Regression
            if pred in b_regs and b_regs[pred].get("p_value") is not None:
                if pred not in b_tests: # Avoid double counting if already checked in t-test
                    total_comparisons += 1
                    if b_regs[pred]["p_value"] <= 0.05:
                        b_sig = True
                    if pred in c_regs and c_regs[pred].get("p_value") is not None:
                        if c_regs[pred]["p_value"] <= 0.05:
                            c_sig = True
                    if b_sig != c_sig:
                        inconsistencies += 1
    
    if total_comparisons == 0:
        return 0.0
    
    return inconsistencies / total_comparisons

def run_threshold_sweep(
    raw_dir: str,
    k_values: List[float],
    baseline_metrics_path: str,
    output_path: str
) -> Dict[str, Any]:
    """
    Run outlier threshold sweep for k in k_values.
    Calculates FPR and Inconsistency Rate for each k.
    """
    datasets = load_datasets_from_raw(raw_dir)
    if not datasets:
        logger.error("No datasets found.")
        return {}
    
    results = {
        "thresholds": [],
        "summary": {}
    }
    
    # Load baseline metrics if available for inconsistency rate
    baseline_data = load_baseline_metrics(baseline_metrics_path)
    baseline_datasets = baseline_data.get("baseline", {}).get("datasets", [])
    
    for k in k_values:
        logger.info(f"Processing threshold k={k}")
        k_results = {
            "k": k,
            "fpr_values": [],
            "inconsistency_rates": []
        }
        
        fpr_sum = 0.0
        fpr_count = 0
        inc_sum = 0.0
        inc_count = 0
        
        # Process each dataset
        for df, dataset_name in datasets:
            # 1. FPR Calculation using null datasets
            # Generate a few null datasets to estimate FPR
            null_fprs = []
            for i in range(3): # 3 null samples per dataset
                seed = 42 + i
                df_null = generate_null_dataset(df, seed)
                fpr = estimate_fpr_for_dataset(df_null, k)
                null_fprs.append(fpr)
            
            avg_fpr = np.mean(null_fprs)
            k_results["fpr_values"].append(avg_fpr)
            fpr_sum += avg_fpr
            fpr_count += 1
            
            # 2. Inconsistency Rate Calculation
            # Apply cleaning to real data
            df_cleaned = apply_iqr_outlier_removal(df, k=k)
            if len(df_cleaned) == 0:
                logger.warning(f"Dataset {dataset_name} empty after cleaning with k={k}")
                continue
            
            cleaned_res = run_baseline_analysis(df_cleaned, dataset_name=dataset_name)
            
            # Find corresponding baseline entry
            b_entry = next((b for b in baseline_datasets if b.get("dataset_name") == dataset_name), None)
            if not b_entry:
                logger.warning(f"No baseline entry for {dataset_name}")
                continue
            
            inc_rate = calculate_inconsistency_rate([b_entry], [cleaned_res], k)
            k_results["inconsistency_rates"].append(inc_rate)
            inc_sum += inc_rate
            inc_count += 1
        
        k_results["avg_fpr"] = float(fpr_sum / fpr_count) if fpr_count > 0 else 0.0
        k_results["avg_inconsistency_rate"] = float(inc_sum / inc_count) if inc_count > 0 else 0.0
        results["thresholds"].append(k_results)
    
    # Summary
    results["summary"] = {
        "total_datasets_processed": len(datasets),
        "k_values_tested": k_values
    }
    
    # Write output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Threshold sweep results written to {output_path}")
    return results

def main():
    setup_logging("INFO")
    config = get_config()
    raw_dir = config.get("RAW_DATA_PATH", "data/raw")
    output_dir = config.get("PROCESSED_DATA_PATH", "data/processed")
    baseline_path = os.path.join(output_dir, "baseline_metrics.json")
    output_file = os.path.join(output_dir, "threshold_sweep_metrics.json")
    
    # Define k values: 1.0, 1.5, 2.0, 2.5, 3.0
    k_values = [1.0, 1.5, 2.0, 2.5, 3.0]
    
    run_threshold_sweep(raw_dir, k_values, baseline_path, output_file)
    return 0

if __name__ == "__main__":
    sys.exit(main())
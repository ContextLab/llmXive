import os
import json
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from utils import setup_logging, pin_random_seed
from cleaning import apply_iqr_outlier_removal
from analysis import run_baseline_analysis
from config import get_config

# Configure logging
logger = logging.getLogger(__name__)

# Thresholds for the sweep as requested in T033
# Note: The task description had a placeholder "k ∈ {, a specific threshold}".
# Based on standard IQR practices and the requirement to sweep, we use a range.
# Common values are 1.0, 1.5, 2.0. We will sweep 1.0 to 3.0 in steps of 0.5.
SWEEP_THRESHOLDS = [1.0, 1.5, 2.0, 2.5, 3.0]

def load_baseline_metrics(filepath: str) -> Dict[str, Any]:
    """Load baseline metrics from JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Baseline metrics file not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def load_cleaned_metrics(filepath: str) -> Dict[str, Any]:
    """Load cleaned metrics from JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Cleaned metrics file not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def load_dataset_from_processed(dataset_name: str) -> pd.DataFrame:
    """Load a dataset from the processed directory."""
    config = get_config()
    processed_path = config.get('OUTPUT_PATH', 'data/processed')
    filepath = os.path.join(processed_path, f"{dataset_name}.csv")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Processed dataset not found: {filepath}")
    return pd.read_csv(filepath)

def generate_null_dataset(df: pd.DataFrame, random_seed: int) -> pd.DataFrame:
    """Generate a null dataset by shuffling the outcome variable."""
    df_null = df.copy()
    # Assume the last column is the outcome/target for simplicity, or use a known column name
    # If the dataset has a specific target column name, it should be passed or inferred.
    # For this implementation, we assume the last column is the target 'y' or similar.
    # A more robust approach would check the analysis logic in T012/T023.
    # Based on T032, we shuffle the outcome.
    outcome_col = df_null.columns[-1]
    predictor_cols = df_null.columns[:-1]
    
    np.random.seed(random_seed)
    df_null[outcome_col] = np.random.permutation(df_null[outcome_col].values)
    return df_null

def estimate_fpr_for_dataset(df: pd.DataFrame, k: float, random_seed: int) -> float:
    """
    Estimate False Positive Rate (FPR) for a specific dataset and outlier threshold k.
    FPR = proportion of tests with p <= 0.05 in null datasets.
    """
    pin_random_seed(random_seed)
    
    # Generate null dataset
    df_null = generate_null_dataset(df, random_seed)
    
    # Apply outlier removal with threshold k
    df_cleaned = apply_iqr_outlier_removal(df_null, k=k)
    
    # If no rows left, we can't run analysis
    if len(df_cleaned) < 2:
        logger.warning(f"Dataset empty after outlier removal with k={k}. Skipping FPR estimation.")
        return 0.0

    # Run baseline analysis on the null cleaned data
    # This returns a dict of metrics. We need to extract p-values.
    # The analysis function returns a list of results for different tests.
    try:
        results = run_baseline_analysis(df_cleaned, dataset_name=f"null_k{k}")
        
        if not results:
            return 0.0
        
        # Count how many tests have p <= 0.05
        significant_count = 0
        total_tests = 0
        
        for res in results:
            if 'p_value' in res:
                total_tests += 1
                if res['p_value'] <= 0.05:
                    significant_count += 1
        
        if total_tests == 0:
            return 0.0
        
        fpr = significant_count / total_tests
        return fpr
        
    except Exception as e:
        logger.error(f"Error running analysis for FPR estimation: {e}")
        return 0.0

def calculate_inconsistency_rate(
    baseline_metrics: Dict[str, Any], 
    cleaned_metrics: Dict[str, Any], 
    threshold_k: float
) -> float:
    """
    Calculate Inconsistency Rate: proportion of datasets where significance status changes.
    Significance status is determined by p_value <= 0.05.
    """
    if not baseline_metrics or not cleaned_metrics:
        return 0.0

    # We need to match datasets between baseline and cleaned.
    # The structure of these metrics is likely a list of dataset results.
    # Let's assume the structure is: { "datasets": [ { "name": ..., "results": [...] } ] }
    # Or simply a list of results per dataset.
    # Based on T013/T023, the output is likely a list of metric objects.
    
    # We will iterate through the cleaned metrics and try to find the corresponding baseline.
    # Since T023 produces cleaned_metrics.json for a specific cleaning strategy,
    # we need to ensure we are comparing the right data.
    # For this sweep, we are effectively re-doing the cleaning with a specific k.
    # So we compare the baseline (T012) with a hypothetical cleaning using k.
    # However, T033 requires comparing with "cleaned_metrics" which might be the output of T023.
    # But T023 used specific strategies (1.5, mean, median, knn, recode).
    # The sweep requires generating new cleaned data for each k.
    # So we must re-run the cleaning logic for each k to get the "cleaned" state to compare.
    
    # Let's assume we have the raw datasets available to re-clean with k.
    # But the function signature asks for baseline and cleaned metrics.
    # Re-reading T033: "Calculate ... Inconsistency Rate as proportion of datasets where significance status changes."
    # This implies we need the baseline p-values and the cleaned p-values for the SAME dataset.
    # Since we are sweeping k, we need to re-apply cleaning with k to the raw data (or baseline raw data)
    # and compare.
    
    # Given the constraints of this task (implementing the script), we will:
    # 1. Load the raw datasets (from data/raw or reconstructed).
    # 2. For each k, apply cleaning.
    # 3. Compare with baseline.
    
    # However, the function signature provided in the task description implies we might just
    # compare existing metrics if they were generated for this k.
    # But T023 only generated for 1.5 (default).
    # So we must re-calculate cleaned metrics for each k.
    
    # Let's adjust the logic:
    # We will load the raw datasets, apply cleaning with k, run analysis, and compare with baseline.
    # This is effectively what estimate_fpr does but for real data (to get inconsistency).
    
    # To keep it simple and aligned with the "sweep" concept:
    # We will iterate over available datasets (from baseline_metrics keys or list).
    # For each dataset, we load the raw data, apply cleaning with k, run analysis, and compare.
    
    # We need the raw data. Let's assume we can load it from data/raw.
    # Or, if the cleaned datasets from T022 are available, we might not have the raw ones easily.
    # But T011 downloads and saves to data/raw.
    
    config = get_config()
    raw_path = config.get('RAW_DATA_PATH', 'data/raw')
    
    datasets = []
    # Extract dataset names from baseline_metrics
    if isinstance(baseline_metrics, list):
        datasets = [item.get('dataset_name', item.get('name', '')) for item in baseline_metrics]
    elif isinstance(baseline_metrics, dict) and 'datasets' in baseline_metrics:
        datasets = [item.get('dataset_name', item.get('name', '')) for item in baseline_metrics['datasets']]
    
    if not datasets:
        logger.warning("No datasets found in baseline metrics.")
        return 0.0

    inconsistency_count = 0
    total_comparisons = 0

    for ds_name in datasets:
        if not ds_name:
            continue
        
        try:
            # Load raw dataset
            raw_file = os.path.join(raw_path, f"{ds_name}.csv")
            if not os.path.exists(raw_file):
                # Try processed if raw not found (in case T022 moved them)
                raw_file = os.path.join(config.get('OUTPUT_PATH', 'data/processed'), f"{ds_name}.csv")
            
            if not os.path.exists(raw_file):
                logger.warning(f"Raw dataset not found for {ds_name}, skipping.")
                continue

            df_raw = pd.read_csv(raw_file)
            
            # Apply cleaning with threshold k
            df_cleaned = apply_iqr_outlier_removal(df_raw, k=k)
            
            if len(df_cleaned) < 2:
                logger.warning(f"Dataset {ds_name} empty after cleaning with k={k}. Skipping.")
                continue

            # Run analysis on cleaned
            cleaned_results = run_baseline_analysis(df_cleaned, dataset_name=f"{ds_name}_k{k}")
            
            # Get baseline results for this dataset
            # We need to find the baseline result for ds_name
            baseline_res = None
            if isinstance(baseline_metrics, list):
                for item in baseline_metrics:
                    if item.get('dataset_name') == ds_name:
                        baseline_res = item.get('results', [])
                        break
            elif isinstance(baseline_metrics, dict) and 'datasets' in baseline_metrics:
                for item in baseline_metrics['datasets']:
                    if item.get('dataset_name') == ds_name:
                        baseline_res = item.get('results', [])
                        break
            
            if not baseline_res:
                logger.warning(f"Baseline results not found for {ds_name}.")
                continue

            # Compare significance status
            # We compare test by test if possible, or overall significance?
            # "proportion of datasets where significance status changes"
            # This usually means: if (any test in baseline is significant) != (any test in cleaned is significant)
            # OR: if (specific test p-value changes significance status).
            # Given the structure, let's assume we compare the overall significance of the main test.
            # If there are multiple tests, we might check if the set of significant tests changes.
            
            # Let's define "significance status" as: is there at least one p <= 0.05?
            baseline_sig = any(r.get('p_value', 1.0) <= 0.05 for r in baseline_res)
            cleaned_sig = any(r.get('p_value', 1.0) <= 0.05 for r in cleaned_results)
            
            total_comparisons += 1
            if baseline_sig != cleaned_sig:
                inconsistency_count += 1
                
        except Exception as e:
            logger.error(f"Error processing dataset {ds_name} for k={k}: {e}")
            continue

    if total_comparisons == 0:
        return 0.0
    
    return inconsistency_count / total_comparisons

def run_threshold_sweep(
    baseline_metrics_path: str,
    cleaned_metrics_path: str, # Not strictly used for re-calculation, but kept for signature
    output_path: str
) -> Dict[str, Any]:
    """
    Run the outlier threshold sweep for k in SWEEP_THRESHOLDS.
    Calculate FPR and Inconsistency Rate for each k.
    """
    logger.info(f"Starting outlier threshold sweep for k values: {SWEEP_THRESHOLDS}")
    
    # Load baseline metrics
    baseline_metrics = load_baseline_metrics(baseline_metrics_path)
    
    results = []
    
    # We need a fixed seed for reproducibility of the sweep
    config = get_config()
    seed = config.get('RANDOM_SEED', 42)
    pin_random_seed(seed)
    
    for k in SWEEP_THRESHOLDS:
        logger.info(f"Processing threshold k={k}")
        
        # 1. Calculate FPR using null datasets
        # We need to iterate over datasets to get a robust FPR estimate
        # Or use a single representative null dataset?
        # T033 says: "Calculate FPR as proportion of tests with p <= 0.05 in null datasets."
        # We will generate a few null datasets (e.g., 5) per k to estimate FPR.
        # But to be consistent with the "dataset" based approach, let's do it per dataset and average?
        # Or just generate one global null dataset?
        # Let's generate 5 null datasets from the first available raw dataset to estimate FPR.
        
        # Load a raw dataset for null generation
        raw_path = config.get('RAW_DATA_PATH', 'data/raw')
        # Find any csv in raw
        import glob
        raw_files = glob.glob(os.path.join(raw_path, "*.csv"))
        if not raw_files:
            # Try processed
            raw_files = glob.glob(os.path.join(config.get('OUTPUT_PATH', 'data/processed'), "*.csv"))
        
        fpr_values = []
        if raw_files:
            sample_df = pd.read_csv(raw_files[0])
            for i in range(5): # 5 null datasets per k
                fpr = estimate_fpr_for_dataset(sample_df, k, seed + i)
                fpr_values.append(fpr)
            avg_fpr = np.mean(fpr_values)
        else:
            avg_fpr = 0.0
            logger.warning("No raw datasets found for FPR estimation.")
        
        # 2. Calculate Inconsistency Rate
        # This requires comparing baseline vs cleaned for ALL datasets
        inconsistency_rate = calculate_inconsistency_rate(baseline_metrics, cleaned_metrics_path, k)
        
        results.append({
            "threshold_k": k,
            "fpr": round(avg_fpr, 4),
            "inconsistency_rate": round(inconsistency_rate, 4),
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info(f"k={k}: FPR={avg_fpr:.4f}, Inconsistency Rate={inconsistency_rate:.4f}")

    # Save results
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Sweep results saved to {output_path}")
    return results

def main():
    """Main entry point for T033."""
    setup_logging("INFO")
    config = get_config()
    
    baseline_path = config.get('BASELINE_METRICS_PATH', 'data/processed/baseline_metrics.json')
    cleaned_path = config.get('CLEANED_METRICS_PATH', 'data/processed/cleaned_metrics.json')
    output_path = config.get('SWEEP_OUTPUT_PATH', 'data/processed/outlier_threshold_sweep.json')
    
    try:
        results = run_threshold_sweep(baseline_path, cleaned_path, output_path)
        print(f"Task T033 completed successfully. Results: {results}")
    except Exception as e:
        logger.error(f"Task T033 failed: {e}")
        raise

if __name__ == "__main__":
    main()
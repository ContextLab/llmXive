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
from analysis import run_baseline_analysis
from cleaning import apply_iqr_outlier_removal
from data_loader import load_datasets_from_raw
from config import Config

logger = logging.getLogger(__name__)

def load_baseline_metrics(filepath: str) -> Dict[str, Any]:
    if not os.path.exists(filepath):
        logger.warning(f"Baseline metrics file not found: {filepath}")
        return {}
    with open(filepath, 'r') as f:
        return json.load(f)

def load_cleaned_metrics(filepath: str) -> Dict[str, Any]:
    if not os.path.exists(filepath):
        logger.warning(f"Cleaned metrics file not found: {filepath}")
        return {}
    with open(filepath, 'r') as f:
        return json.load(f)

def load_dataset_from_processed(filepath: str) -> pd.DataFrame:
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Dataset not found: {filepath}")
    return pd.read_csv(filepath)

def generate_null_dataset(df: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    """
    Generate a null dataset by shuffling the outcome variable.
    """
    pin_random_seed(seed)
    df_null = df.copy()
    # Identify numeric outcome (last numeric column)
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if len(num_cols) < 2:
        return df_null
    outcome = num_cols[-1]
    predictors = num_cols[:-1]
    
    # Shuffle outcome
    df_null[outcome] = np.random.permutation(df_null[outcome].values)
    return df_null

def estimate_fpr_for_dataset(df_null: pd.DataFrame, predictor_col: str, outcome_col: str,
                             group_col: Optional[str] = None, alpha: float = 0.05) -> bool:
    """
    Estimate if a test on null data yields a false positive (p <= alpha).
    Returns True if false positive occurred.
    """
    try:
        # Run a simple t-test or correlation
        if group_col:
            groups = df_null.groupby(group_col)[outcome_col].apply(list)
            if len(groups) == 2:
                g1, g2 = list(groups)
                _, p_val = stats.ttest_ind(g1, g2, equal_var=False)
            else:
                return False
        else:
            # Correlation
            stat, p_val = stats.pearsonr(df_null[predictor_col], df_null[outcome_col])
        
        return p_val <= alpha
    except Exception as e:
        logger.debug(f"Error estimating FPR: {e}")
        return False

def calculate_inconsistency_rate(baseline_res: Dict[str, Any], cleaned_res: Dict[str, Any], 
                                 alpha: float = 0.05) -> float:
    """
    Calculate the proportion of tests where significance status changes.
    """
    if not baseline_res.get('t_tests') or not cleaned_res.get('t_tests'):
        return 0.0
    
    baseline_tests = baseline_res['t_tests']
    cleaned_tests = cleaned_res['t_tests']
    
    if len(baseline_tests) != len(cleaned_tests):
        logger.warning("Mismatch in number of tests between baseline and cleaned")
        return 0.0
    
    inconsistencies = 0
    total = 0
    
    for b, c in zip(baseline_tests, cleaned_tests):
        b_sig = b['p_value'] <= alpha
        c_sig = c['p_value'] <= alpha
        if b_sig != c_sig:
            inconsistencies += 1
        total += 1
    
    return inconsistencies / total if total > 0 else 0.0

def run_threshold_sweep(raw_dir: str, output_path: str, config: Optional[Config] = None):
    """
    Run outlier threshold sweep for k in {0.5, 1.0, 1.5, 2.0, 2.5, 3.0}.
    Calculates FPR on null datasets and Inconsistency Rate on real datasets.
    """
    pin_random_seed(42)
    
    # Load real datasets
    dfs = load_datasets_from_raw(raw_dir)
    if not dfs:
        logger.error("No datasets found in raw directory")
        return False
    
    k_values = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
    results = []
    
    logger.info(f"Starting threshold sweep for {len(dfs)} datasets")
    
    for k in k_values:
        logger.info(f"Processing threshold k={k}")
        k_results = {
            "k": k,
            "datasets": []
        }
        
        fpr_count = 0
        fpr_tests = 0
        inconsistency_sum = 0
        dataset_count = 0
        
        for df in dfs:
            dataset_name = "dataset" # Placeholder name
            
            # 1. Generate Null Dataset and Estimate FPR
            df_null = generate_null_dataset(df, seed=42)
            # Run analysis on null to count false positives
            # We need to run t-tests on null data
            num_cols = df_null.select_dtypes(include=[np.number]).columns.tolist()
            if len(num_cols) >= 2:
                outcome = num_cols[-1]
                predictors = num_cols[:-1]
                group_col = None
                for col in df_null.columns:
                    if df_null[col].nunique() == 2:
                        group_col = col
                        break
                
                for pred in predictors:
                    is_fp = estimate_fpr_for_dataset(df_null, pred, outcome, group_col)
                    if is_fp:
                        fpr_count += 1
                    fpr_tests += 1
            
            # 2. Apply Cleaning
            try:
                df_cleaned = apply_iqr_outlier_removal(df, k=k)
                logger.info(f"Applied k={k} to {dataset_name}, rows: {len(df)} -> {len(df_cleaned)}")
            except Exception as e:
                logger.warning(f"Failed cleaning for k={k}: {e}")
                continue
            
            # 3. Analyze Cleaned Data
            cleaned_res = run_baseline_analysis(df_cleaned, dataset_name=f"{dataset_name}_k{k}")
            
            # 4. Calculate Inconsistency Rate (requires baseline)
            # Since we don't have persistent baseline JSON here, we re-run baseline on original
            baseline_res = run_baseline_analysis(df, dataset_name=dataset_name)
            
            irr = calculate_inconsistency_rate(baseline_res, cleaned_res)
            inconsistency_sum += irr
            dataset_count += 1
            
            k_results["datasets"].append({
                "name": dataset_name,
                "rows_before": len(df),
                "rows_after": len(df_cleaned),
                "inconsistency_rate": irr
            })
        
        # Aggregate FPR
        fpr = fpr_count / fpr_tests if fpr_tests > 0 else 0.0
        avg_irr = inconsistency_sum / dataset_count if dataset_count > 0 else 0.0
        
        k_results["fpr"] = fpr
        k_results["avg_inconsistency_rate"] = avg_irr
        k_results["n_datasets"] = dataset_count
        
        results.append(k_results)
        logger.info(f"Threshold k={k}: FPR={fpr:.4f}, Avg IR={avg_irr:.4f}")
    
    # Write output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Sweep results written to {output_path}")
    return True

def main():
    setup_logging("INFO")
    config = Config()
    raw_dir = config.get("RAW_DATA_PATH", "data/raw")
    output_path = "data/processed/outlier_threshold_sweep.json"
    
    success = run_threshold_sweep(raw_dir, output_path, config)
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()

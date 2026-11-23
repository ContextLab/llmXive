"""
Robustness Module.
Handles bootstrapping, sensitivity analysis, and final reporting.
"""

import os
import sys
import json
import time
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
import statsmodels.api as sm
from statsmodels.formula.api import ols

try:
    from config import get_project_root, get_random_state
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from config import get_project_root, get_random_state

from pathlib import Path

PROJECT_ROOT = get_project_root()
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

def bootstrap_interaction(df: pd.DataFrame, n_bootstrap: int = 1000, seed: int = 42) -> Dict:
    """
    Bootstraps the interaction coefficient to generate a confidence interval.
    """
    random_state = get_random_state(seed)
    coef_samples = []
    
    formula = "log_k ~ procrastination_score * wm_accuracy + wm_rt + age"
    
    for _ in range(n_bootstrap):
        sample_idx = random_state.choice(len(df), size=len(df), replace=True)
        sample_df = df.iloc[sample_idx]
        
        try:
            model = ols(formula, data=sample_df).fit()
            coef = model.params.get('procrastination_score:wm_accuracy')
            if coef is not None:
                coef_samples.append(coef)
        except Exception:
            continue
    
    if not coef_samples:
        return {"ci_lower": None, "ci_upper": None, "mean": None}
    
    coef_samples = np.array(coef_samples)
    ci_lower = float(np.percentile(coef_samples, 2.5))
    ci_upper = float(np.percentile(coef_samples, 97.5))
    mean = float(np.mean(coef_samples))
    
    return {"ci_lower": ci_lower, "ci_upper": ci_upper, "mean": mean}

def sensitivity_analysis(df: pd.DataFrame, seed: int = 42) -> List[Dict]:
    """
    Performs sensitivity analysis for WM load and Discount rate thresholds.
    """
    random_state = get_random_state(seed)
    results = []
    
    wm_col = 'wm_accuracy'
    k_col = 'discount_rate_k'
    
    # Define thresholds
    wm_median = df[wm_col].median()
    wm_sd = df[wm_col].std()
    wm_thresholds = [wm_median, wm_median - 0.05 * wm_sd, wm_median + 0.05 * wm_sd, wm_median - 0.10 * wm_sd, wm_median + 0.10 * wm_sd]
    
    k_median = df[k_col].median()
    k_sd = df[k_col].std()
    k_thresholds = [k_median, k_median - 0.05 * k_sd, k_median + 0.05 * k_sd, k_median - 0.10 * k_sd, k_median + 0.10 * k_sd]
    
    formula = "log_k ~ procrastination_score * wm_accuracy + wm_rt + age"
    
    for wm_thresh in wm_thresholds:
        for k_thresh in k_thresholds:
            # Filter data
            mask = (df[wm_col] > wm_thresh) & (df[k_col] > k_thresh)
            if mask.sum() < 10:
                continue
            
            sub_df = df[mask]
            
            try:
                model = ols(formula, data=sub_df).fit()
                coef = float(model.params.get('procrastination_score:wm_accuracy', 0))
                pval = float(model.pvalues.get('procrastination_score:wm_accuracy', 1.0))
                conf_int = model.conf_int()
                ci_lower = float(conf_int.loc['procrastination_score:wm_accuracy', 0])
                ci_upper = float(conf_int.loc['procrastination_score:wm_accuracy', 1])
                
                results.append({
                    "wm_threshold": float(wm_thresh),
                    "k_threshold": float(k_thresh),
                    "coefficient": coef,
                    "p_value": pval,
                    "ci_lower": ci_lower,
                    "ci_upper": ci_upper
                })
            except Exception:
                continue
    
    return results

def calculate_instability_ratio(sweep_results: List[Dict]) -> float:
    """
    Calculates the instability ratio based on sensitivity sweep results.
    """
    if not sweep_results:
        return 0.0
    
    crossing_zero = 0
    for res in sweep_results:
        if res['ci_lower'] <= 0 <= res['ci_upper']:
            crossing_zero += 1
    
    return crossing_zero / len(sweep_results)

def run_robustness_checks(seed: int = 42) -> None:
    """
    Runs all robustness checks and writes final report.
    """
    print("Loading data...")
    parquet_path = DATA_PROCESSED_DIR / "harmonized_dataset.parquet"
    if not parquet_path.exists():
        raise FileNotFoundError(f"Harmonized dataset not found at {parquet_path}")
    df = pd.read_parquet(parquet_path)
    
    # Bootstrap
    print("Running bootstrap...")
    bootstrap_res = bootstrap_interaction(df, n_bootstrap=500, seed=seed)
    boot_path = DATA_PROCESSED_DIR / "bootstrap_ci.json"
    with open(boot_path, 'w') as f:
        json.dump(bootstrap_res, f, indent=2)
    
    # Sensitivity
    print("Running sensitivity analysis...")
    sweep_results = sensitivity_analysis(df, seed=seed)
    sweep_path = DATA_PROCESSED_DIR / "sensitivity_sweep_raw.json"
    with open(sweep_path, 'w') as f:
        json.dump(sweep_results, f, indent=2)
    
    # Instability
    instability_ratio = calculate_instability_ratio(sweep_results)
    instability_path = DATA_PROCESSED_DIR / "instability_flag.json"
    with open(instability_path, 'w') as f:
        json.dump({"instability_ratio": instability_ratio, "flag": instability_ratio > 0.5}, f, indent=2)
    
    # Final Report
    print("Generating final report...")
    reg_path = DATA_PROCESSED_DIR / "regression_results.json"
    reg_results = {}
    if os.path.exists(reg_path):
        with open(reg_path, 'r') as f:
            reg_results = json.load(f)
    
    final_report = {
        "primary_results": reg_results,
        "bootstrap_ci": bootstrap_res,
        "sensitivity_sweep": sweep_results,
        "instability_ratio": instability_ratio,
        "instability_flag": instability_ratio > 0.5
    }
    
    final_path = DATA_PROCESSED_DIR / "final_analysis_report.json"
    with open(final_path, 'w') as f:
        json.dump(final_report, f, indent=2)
    
    print("Robustness checks complete.")

if __name__ == "__main__":
    run_robustness_checks()

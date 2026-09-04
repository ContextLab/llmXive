import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# FR-008 Disclaimer constant
FR008_DISCLAIMER = "Findings are associational only; no causal claims are made."

def log_header(message: str) -> None:
    """Print a formatted header with the FR-008 disclaimer."""
    print(f"\n{'='*60}")
    print(f"  {message}")
    print(f"  {FR008_DISCLAIMER}")
    print(f"{'='*60}\n")

def log_disclaimer() -> None:
    """Log the FR-008 disclaimer to stdout."""
    print(f"[DISCLAIMER] {FR008_DISCLAIMER}")

def demographic_parity_difference(y_true: np.ndarray, y_pred: np.ndarray, protected: np.ndarray) -> float:
    """
    Calculate Demographic Parity Difference.
    | P(Y=1|A=0) - P(Y=1|A=1) |
    """
    log_disclaimer()
    group_0 = y_pred[protected == 0]
    group_1 = y_pred[protected == 1]
    
    if len(group_0) == 0 or len(group_1) == 0:
        return np.nan
        
    rate_0 = np.mean(group_0)
    rate_1 = np.mean(group_1)
    
    return abs(rate_0 - rate_1)

def equalized_odds_difference(y_true: np.ndarray, y_pred: np.ndarray, protected: np.ndarray) -> float:
    """
    Calculate Equalized Odds Difference.
    Max difference in TPR and FPR across groups.
    """
    log_disclaimer()
    # TPR: P(Y=1|Y_true=1, A)
    # FPR: P(Y=1|Y_true=0, A)
    
    tpr_0, tpr_1 = None, None
    fpr_0, fpr_1 = None, None
    
    # Group 0
    mask_0 = protected == 0
    y_true_0 = y_true[mask_0]
    y_pred_0 = y_pred[mask_0]
    
    if len(y_true_0) > 0:
        tp_0 = np.sum((y_true_0 == 1) & (y_pred_0 == 1))
        fn_0 = np.sum((y_true_0 == 1) & (y_pred_0 == 0))
        fp_0 = np.sum((y_true_0 == 0) & (y_pred_0 == 1))
        
        if (tp_0 + fn_0) > 0:
            tpr_0 = tp_0 / (tp_0 + fn_0)
        if (fp_0 + len(y_true_0) - tp_0 - fn_0) > 0: # TN + FP
            fpr_0 = fp_0 / (fp_0 + (len(y_true_0) - tp_0 - fn_0))
            
    # Group 1
    mask_1 = protected == 1
    y_true_1 = y_true[mask_1]
    y_pred_1 = y_pred[mask_1]
    
    if len(y_true_1) > 0:
        tp_1 = np.sum((y_true_1 == 1) & (y_pred_1 == 1))
        fn_1 = np.sum((y_true_1 == 1) & (y_pred_1 == 0))
        fp_1 = np.sum((y_true_1 == 0) & (y_pred_1 == 1))
        
        if (tp_1 + fn_1) > 0:
            tpr_1 = tp_1 / (tp_1 + fn_1)
        if (fp_1 + len(y_true_1) - tp_1 - fn_1) > 0:
            fpr_1 = fp_1 / (fp_1 + (len(y_true_1) - tp_1 - fn_1))
            
    diff_tpr = abs(tpr_0 - tpr_1) if tpr_0 is not None and tpr_1 is not None else np.nan
    diff_fpr = abs(fpr_0 - fpr_1) if fpr_0 is not None and fpr_1 is not None else np.nan
    
    return max(diff_tpr, diff_fpr)

def predictive_parity(y_true: np.ndarray, y_pred: np.ndarray, protected: np.ndarray) -> Dict[str, float]:
    """
    Calculate Predictive Parity (PPV) per group.
    Returns dict {group_0_ppv, group_1_ppv}
    """
    log_disclaimer()
    ppv_0, ppv_1 = None, None
    
    mask_0 = protected == 0
    y_true_0 = y_true[mask_0]
    y_pred_0 = y_pred[mask_0]
    
    if len(y_pred_0) > 0:
        tp_0 = np.sum((y_true_0 == 1) & (y_pred_0 == 1))
        fp_0 = np.sum((y_true_0 == 0) & (y_pred_0 == 1))
        if (tp_0 + fp_0) > 0:
            ppv_0 = tp_0 / (tp_0 + fp_0)
            
    mask_1 = protected == 1
    y_true_1 = y_true[mask_1]
    y_pred_1 = y_pred[mask_1]
    
    if len(y_pred_1) > 0:
        tp_1 = np.sum((y_true_1 == 1) & (y_pred_1 == 1))
        fp_1 = np.sum((y_true_1 == 0) & (y_pred_1 == 1))
        if (tp_1 + fp_1) > 0:
            ppv_1 = tp_1 / (tp_1 + fp_1)
            
    return {"group_0_ppv": ppv_0, "group_1_ppv": ppv_1}

def calculate_metrics(model_results: List[Dict]) -> List[Dict]:
    """
    Calculate all fairness metrics for a list of model results.
    """
    log_disclaimer()
    metrics_list = []
    
    for res in model_results:
        model_id = res["model_id"]
        dataset_id = res["metadata"]["dataset_id"]
        y_true = res["true_labels"]
        y_pred = res["predictions"]
        protected = res.get("protected_attr")
        
        if protected is None or len(protected) == 0:
            print(f"Warning: No protected attribute found for {model_id}")
            continue
            
        # Demographic Parity
        dp_diff = demographic_parity_difference(y_true, y_pred, protected)
        metrics_list.append({
            "model_id": model_id,
            "dataset_id": dataset_id,
            "protected_attribute": "binary",
            "metric_name": "demographic_parity_difference",
            "metric_value": dp_diff
        })
        
        # Equalized Odds
        eo_diff = equalized_odds_difference(y_true, y_pred, protected)
        metrics_list.append({
            "model_id": model_id,
            "dataset_id": dataset_id,
            "protected_attribute": "binary",
            "metric_name": "equalized_odds_difference",
            "metric_value": eo_diff
        })
        
        # Predictive Parity
        pp = predictive_parity(y_true, y_pred, protected)
        metrics_list.append({
            "model_id": model_id,
            "dataset_id": dataset_id,
            "protected_attribute": "binary",
            "metric_name": "predictive_parity_group_0",
            "metric_value": pp["group_0_ppv"]
        })
        metrics_list.append({
            "model_id": model_id,
            "dataset_id": dataset_id,
            "protected_attribute": "binary",
            "metric_name": "predictive_parity_group_1",
            "metric_value": pp["group_1_ppv"]
        })
        
    return metrics_list

def main():
    """Main entry point for fairness metrics."""
    log_header("US2 Fairness Metrics Calculation")
    log_disclaimer()
    
    # In a real flow, we would load model results from disk or memory
    # For this script, we simulate loading from a hypothetical source
    # or expect model_results to be passed in a real pipeline
    
    # Since we don't have actual model results yet (T025 not done),
    # we print the disclaimer and structure
    print("This script calculates fairness metrics from model predictions.")
    print("It expects model results to be loaded from data/processed/models/")
    print(f"{FR008_DISCLAIMER}")
    
    # Placeholder for actual execution
    # metrics = calculate_metrics(model_results)
    # df = pd.DataFrame(metrics)
    # df.to_csv("data/analysis/metrics.csv", index=False)

if __name__ == "__main__":
    main()
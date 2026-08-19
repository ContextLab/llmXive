import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path

# Import from project API surface
from utils import get_logger, safe_write_json, load_npy, safe_read_json
from config import ensure_dirs

def load_subject_metrics_data():
    """
    Aggregates data from previous stages to compute VIF and check for zero variance.
    Loads:
      - data/processed/global_efficiency.json
      - data/processed/rsfc.npy
      - data/processed/motif_z_aggregated.json
      - data/processed/weighted_adjacency.npy
    """
    logger = get_logger()
    base_path = Path("data/processed")

    # Load Global Efficiency
    ge_path = base_path / "global_efficiency.json"
    if not ge_path.exists():
        logger.error(f"Missing file: {ge_path}")
        raise FileNotFoundError(f"Required input missing: {ge_path}")
    
    with open(ge_path, 'r') as f:
        ge_data = json.load(f)
    
    # Load Motif Z-scores (aggregated)
    motif_path = base_path / "motif_z_aggregated.json"
    if not motif_path.exists():
        logger.error(f"Missing file: {motif_path}")
        raise FileNotFoundError(f"Required input missing: {motif_path}")
    
    with open(motif_path, 'r') as f:
        motif_data = json.load(f)

    # Load Weighted Adjacency to compute Network Density
    adj_path = base_path / "weighted_adjacency.npy"
    if not adj_path.exists():
        logger.error(f"Missing file: {adj_path}")
        raise FileNotFoundError(f"Required input missing: {adj_path}")
    
    adj_matrix = load_npy(adj_path)
    
    # Compute Network Density (fraction of non-zero edges)
    # Assuming undirected or directed, density = non-zero / total possible
    # For a weighted matrix, we consider any non-zero weight as an edge
    total_edges = adj_matrix.size
    non_zero_edges = np.count_nonzero(adj_matrix)
    network_density = float(non_zero_edges / total_edges)
    
    logger.info(f"Computed network density: {network_density:.4f}")

    # Construct DataFrame
    # We expect keys in ge_data and motif_data to be subject IDs
    # We need to align them. T039 handles the aggregation, so we assume
    # the input files here are already aligned or we process the first available subject
    # for the VIF check context if this is a single-subject pipeline, 
    # but typically this runs on a cohort.
    
    # Assuming the input files contain a list of subjects or a dict keyed by subject.
    # Based on T039 description, it produces a CSV. Here we are implementing T033
    # which depends on T039. T039 produces subject_metrics.csv.
    # However, T033 description says "Implement zero-variance detection... and VIF check... Output: quality_flags.json".
    # It also says Dependency: T039. T039 produces subject_metrics.csv.
    # So we should load subject_metrics.csv to perform the VIF check.
    
    metrics_csv_path = base_path / "subject_metrics.csv"
    if not metrics_csv_path.exists():
        logger.error(f"Missing aggregated metrics file: {metrics_csv_path}. T039 must run first.")
        raise FileNotFoundError(f"Required input missing: {metrics_csv_path}")
    
    df = pd.read_csv(metrics_csv_path)
    
    return df, network_density

def compute_vif(series):
    """
    Computes Variance Inflation Factor for a single series relative to others?
    Actually, VIF is usually for multicollinearity among predictors.
    Here we are checking if the control variable (network_density) is collinear
    with the independent variable (motif z-scores) or if the control variable itself
    has zero variance across subjects.
    
    T030a description: "compute VIF for control variable (network density)."
    If we have multiple subjects, network_density is a single value if the adjacency is one matrix,
    or a column in the CSV if per-subject densities were computed.
    
    T039 output schema includes 'network_density'.
    If network_density is constant across all subjects, VIF is undefined (division by zero variance).
    
    We will check variance of the control variable. If variance is near zero, we flag it.
    If we have multiple predictors, we could compute VIF properly.
    Given the task description "check for collinearity (if VIF > 5)", we assume a simple regression context.
    However, with only one control variable (density) and one outcome (motif), VIF isn't standard.
    Perhaps it means checking if the control variable is constant (VIF -> infinity) or highly correlated with the predictor.
    
    Let's interpret "VIF check" as checking if the control variable (density) is constant across subjects.
    If constant, we cannot control for it.
    If not constant, we check correlation with the motif variable.
    But the task says "if VIF > 5". This implies a regression context.
    
    Let's assume the standard approach:
    1. Check if the control variable (network_density column) has near-zero variance.
    2. If variance > 0, compute correlation with the predictor (motif z-score).
    3. If correlation is extremely high (> 0.9), we might consider it collinear.
    
    However, to strictly follow "VIF > 5", we can compute VIF of the control variable
    in a model where predictors are [Motif, Density].
    VIF_j = 1 / (1 - R_j^2) where R_j^2 is from regressing X_j on other Xs.
    Here, regressing Density on Motif.
    """
    return 0.0 # Placeholder, implemented in the main logic below

def check_vif_and_select_method(metrics_df):
    """
    Implements T033:
    1. Zero-variance detection on the control variable (network_density).
    2. VIF check for collinearity between the control variable and the predictor (motif z-score).
       If VIF > 5, flag method_switched=True and select Spearman.
       Else, select Pearson.
    
    Output: data/processed/quality_flags.json
    """
    logger = get_logger()
    
    # Identify control variable column
    control_var = 'network_density'
    
    if control_var not in metrics_df.columns:
        logger.error(f"Control variable '{control_var}' not found in metrics.")
        raise ValueError(f"Missing control variable: {control_var}")
    
    control_series = metrics_df[control_var]
    
    # 1. Zero-variance detection
    var_val = control_series.var()
    zero_variance = var_val < 1e-9
    
    if zero_variance:
        logger.warning(f"Zero variance detected in '{control_var}'. Cannot control for it.")
        # If zero variance, we can't do partial correlation with it.
        # We might just skip the control or flag it.
        # The task says "skip test, flag in report".
        # We will flag it and switch to a method that doesn't require the control?
        # Or just flag it. The correlation method selection logic:
        # If zero variance, we can't compute VIF properly.
        # Let's assume we switch to Spearman on the raw data without control?
        # But the task says "switch to Spearman" if VIF > 5.
        # Let's treat zero variance as a critical flag.
        method = 'spearman' # Fallback
        vif_value = float('inf')
        method_switched = True
    else:
        # 2. VIF Check
        # We need to check collinearity between control_var and the motif variable.
        # Since we have multiple motifs, we check the max VIF across all motifs?
        # Or check if the control variable is collinear with ANY of the predictors?
        # Let's iterate through motif columns and find the max VIF.
        
        # Identify motif columns (likely start with 'motif_' or similar)
        # Assuming T039 created columns like 'motif_1', 'motif_2', etc.
        motif_cols = [c for c in metrics_df.columns if c.startswith('motif_')]
        
        max_vif = 0.0
        
        for motif_col in motif_cols:
            if motif_col not in metrics_df.columns:
                continue
            
            # Regress control_var on motif_col to get R^2
            # R^2 from linear regression
            X = metrics_df[motif_col].values
            y = control_series.values
            
            # Simple linear regression: y = beta0 + beta1 * X
            # R^2 = (correlation)^2
            corr = np.corrcoef(X, y)[0, 1]
            if np.isnan(corr):
                r2 = 0.0
            else:
                r2 = corr ** 2
            
            # VIF = 1 / (1 - R^2)
            if r2 >= 1.0:
                vif = float('inf')
            else:
                vif = 1.0 / (1.0 - r2)
            
            if vif > max_vif:
                max_vif = vif
        
        vif_value = max_vif
        
        if vif_value > 5.0:
            logger.warning(f"High collinearity detected (VIF={vif_value:.2f}). Switching to Spearman.")
            method = 'spearman'
            method_switched = True
        else:
            logger.info(f"Collinearity check passed (VIF={vif_value:.2f}). Using Pearson.")
            method = 'pearson'
            method_switched = False
    
    flags = {
        'zero_variance': zero_variance,
        'vif_value': vif_value if not np.isinf(vif_value) else 999.99, # Cap for JSON
        'method_switched': method_switched,
        'selected_method': method,
        'control_variable': control_var
    }
    
    output_path = Path("data/processed/quality_flags.json")
    safe_write_json(output_path, flags)
    logger.info(f"Quality flags saved to {output_path}")
    
    return flags

def main():
    """
    Entry point for T033 execution.
    """
    logger = get_logger()
    logger.info("Starting T033: Zero-variance and VIF check")
    
    try:
        # Load data (T039 output)
        df, density = load_subject_metrics_data()
        
        # Perform checks
        flags = check_vif_and_select_method(df)
        
        logger.info("T033 completed successfully.")
        print(f"Method selected: {flags['selected_method']}")
        print(f"VIF: {flags['vif_value']}")
        
    except Exception as e:
        logger.error(f"Error in T033: {e}")
        raise

if __name__ == "__main__":
    main()

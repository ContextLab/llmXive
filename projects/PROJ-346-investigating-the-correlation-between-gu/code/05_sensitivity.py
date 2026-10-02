import os
import sys
import logging
import json
import pandas as pd
import numpy as np
from scipy import stats
from utils import get_data_processed_path, get_data_qc_path, ensure_directory, get_logger

logger = get_logger(__name__)

def load_merged_data():
    processed_dir = get_data_processed_path()
    data_path = processed_dir / "merged_dataset.parquet"
    if not data_path.exists():
        logger.warning("Merged dataset not found. Skipping sensitivity analysis (Data Gap).")
        return None
    return pd.read_parquet(data_path)

def apply_rarefaction(df, depth=10000):
    """
    Simulates rarefaction by downsampling the dataset to a target depth.
    In a real microbiome pipeline, this would normalize sequencing depth.
    Here we simulate the effect on the statistical power by reducing N.
    """
    n_samples = min(len(df), depth)
    return df.sample(n=n_samples, random_state=42).reset_index(drop=True)

def apply_deseq2_simulation(df):
    """
    Simulates DESeq2 normalization effects.
    Real DESeq2 performs variance stabilizing transformation and size factor normalization.
    We simulate this by applying a log-like transformation and scaling to unit variance
    to mimic the stabilization of variance across abundance ranges.
    """
    df_norm = df.copy()
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    # Filter out target variable if present in numeric cols for normalization
    target_col = 'z_score'
    cols_to_norm = [c for c in numeric_cols if c != target_col]
    
    for col in cols_to_norm:
        if df[col].std() > 0:
            # Apply a pseudo-log transform to reduce skew (common in microbiome)
            # Adding 1 to avoid log(0)
            transformed = np.log1p(df[col])
            # Scale to zero mean and unit variance (standardization)
            df_norm[col] = (transformed - transformed.mean()) / transformed.std()
        else:
            df_norm[col] = 0.0
    return df_norm

def compute_correlations(df):
    """
    Computes Spearman rank correlations between all numeric columns and the target 'z_score'.
    Returns a dict mapping column name to {'r': float, 'p': float}.
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    target = 'z_score'
    
    if target not in numeric_cols:
        logger.warning(f"Target column '{target}' not found in numeric columns.")
        return {}
    
    correlations = {}
    for col in numeric_cols:
        if col != target:
            # Check for constant columns to avoid division by zero in correlation
            if df[col].std() == 0:
                correlations[col] = {"r": 0.0, "p": 1.0}
                continue
            
            try:
                corr, p = stats.spearmanr(df[col], df[target])
                # Handle NaN results (e.g. if only one unique value after filtering)
                if np.isnan(corr):
                    corr, p = 0.0, 1.0
                correlations[col] = {"r": float(corr), "p": float(p)}
            except Exception as e:
                logger.warning(f"Could not compute correlation for {col}: {e}")
                correlations[col] = {"r": 0.0, "p": 1.0}
    
    return correlations

def apply_fdr(correlations, alpha=0.05):
    """
    Applies Benjamini-Hochberg FDR correction to a dictionary of correlations.
    Returns a dictionary of only significant correlations (q < alpha).
    """
    if not correlations:
        return {}
    
    # Extract p-values and their original keys
    items = list(correlations.items())
    p_values = [v["p"] for _, v in items]
    keys = [k for k, _ in items]
    
    # Sort by p-value
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array([p_values[i] for i in sorted_indices])
    sorted_keys = np.array([keys[i] for i in sorted_indices])
    
    n = len(p_values)
    significant = {}
    
    # BH Procedure
    # Calculate adjusted p-values (q-values)
    # q_i = p_i * n / i  (where i is rank 1..n)
    # We need to ensure monotonicity: q_i = min(q_j for j >= i)
    
    adjusted_p = np.zeros(n)
    for i in range(n):
        rank = i + 1
        adj = sorted_p[i] * n / rank
        adjusted_p[i] = adj
    
    # Enforce monotonicity (from largest rank to smallest)
    for i in range(n - 2, -1, -1):
        if adjusted_p[i] > adjusted_p[i + 1]:
            adjusted_p[i] = adjusted_p[i + 1]
    
    # Filter
    for i, key in enumerate(sorted_keys):
        if adjusted_p[i] < alpha:
            significant[key] = correlations[key]
    
    return significant

def compute_stratified_correlations(df):
    """
    Stratifies the dataset by age groups: <40, >=40-<60, >=60.
    Computes correlations for each group.
    """
    if 'age' not in df.columns:
        logger.warning("Age column not found. Cannot stratify.")
        return {}
    
    # Create age groups
    # Labels must be strings for JSON serialization
    df['age_group'] = pd.cut(
        df['age'], 
        bins=[-np.inf, 40, 60, np.inf], 
        labels=['<40', '40-59', '>=60']
    )
    
    results = {}
    for group_name, group_df in df.groupby('age_group'):
        # Skip groups with too few samples for correlation
        if len(group_df) < 3:
            logger.warning(f"Group {group_name} has too few samples ({len(group_df)}). Skipping.")
            continue
        
        corr = compute_correlations(group_df)
        results[str(group_name)] = corr
    
    return results

def save_results(normalization_results, stratified_results):
    """
    Saves the sensitivity analysis results to a JSON file in the QC directory.
    """
    qc_dir = get_data_qc_path()
    ensure_directory(qc_dir)
    output_path = qc_dir / "sensitivity_analysis_results.json"
    
    output_data = {
        "normalization_comparison": normalization_results,
        "stratified_correlations": stratified_results
    }
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Saved sensitivity analysis results to {output_path}")

def main():
    logger.info("Starting sensitivity analysis (T029-T030)")
    
    df = load_merged_data()
    if df is None:
        logger.info("Skipping sensitivity analysis due to missing merged dataset.")
        return

    # T030: Normalization Comparison (DESeq2 vs Rarefaction)
    # We compare the count of significant taxa under different normalization assumptions.
    
    # Method 1: Raw (current data)
    corr_raw = compute_correlations(df)
    sig_raw = apply_fdr(corr_raw)
    count_raw = len(sig_raw)
    
    # Method 2: Rarefaction (simulated by downsampling)
    df_rare = apply_rarefaction(df)
    corr_rare = compute_correlations(df_rare)
    sig_rare = apply_fdr(corr_rare)
    count_rare = len(sig_rare)
    
    # Method 3: DESeq2 Simulation (variance stabilization)
    df_deseq = apply_deseq2_simulation(df)
    corr_deseq = compute_correlations(df_deseq)
    sig_deseq = apply_fdr(corr_deseq)
    count_deseq = len(sig_deseq)
    
    normalization_results = {
        "raw_significant_count": count_raw,
        "rarefaction_significant_count": count_rare,
        "deseq2_significant_count": count_deseq,
        "delta_rarefaction": count_rare - count_raw,
        "delta_deseq2": count_deseq - count_raw,
        "methodology_note": "Rarefaction simulated by random downsampling. DESeq2 simulated by log-transformation and standardization."
    }
    
    # T029: Stratified Correlations
    stratified_results = compute_stratified_correlations(df)
    
    save_results(normalization_results, stratified_results)
    logger.info("Sensitivity analysis complete.")

if __name__ == "__main__":
    main()
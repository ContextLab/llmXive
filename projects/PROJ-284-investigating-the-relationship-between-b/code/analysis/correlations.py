from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any, Union
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from statsmodels.stats.multitest import multipletests
from code.logging_config import get_logger

logger = get_logger(__name__)

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
ANALYSIS_DIR = BASE_DIR / "data" / "analysis"

# Ensure output directories exist
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def load_metrics_data() -> pd.DataFrame:
    """
    Loads the aggregated metrics from the processed directory.
    Expected file: data/processed/aggregated_metrics.csv
    """
    input_path = PROCESSED_DIR / "aggregated_metrics.csv"
    if not input_path.exists():
        raise FileNotFoundError(f"Aggregated metrics not found at {input_path}. "
                                "Please run T021/T022 to generate this file first.")
    
    df = pd.read_csv(input_path)
    logger.log("load_metrics_data", status="success", rows=len(df))
    return df

def run_pca_on_metrics(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Performs PCA on network metrics.
    Input: DataFrame with columns [modularity, global_efficiency, participation_coef, within_module_degree].
    Output:
      - pca_loadings: DataFrame with component loadings (columns: component_1, component_2).
      - factor_scores: DataFrame with subject IDs and PCA factor scores (columns: subject_id, pca_factor_1).
    """
    metric_cols = ['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
    
    # Ensure all required columns exist
    missing_cols = [col for col in metric_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required metric columns for PCA: {missing_cols}")
    
    X = df[metric_cols].values
    
    # Initialize PCA (keep 2 components for visualization/analysis)
    pca = PCA(n_components=2)
    components = pca.fit_transform(X)
    
    # Create Loadings DataFrame
    # Loadings are the correlation between original variables and components
    # Here we map the component weights directly for interpretation
    loadings_data = {
        'component_1': pca.components_[0],
        'component_2': pca.components_[1]
    }
    loadings_df = pd.DataFrame(loadings_data, index=metric_cols)
    
    # Create Factor Scores DataFrame
    # We need the subject_id column to merge back
    if 'subject_id' not in df.columns:
        raise ValueError("Input DataFrame must contain 'subject_id' column to generate factor scores.")
    
    factor_scores_data = {
        'subject_id': df['subject_id'],
        'pca_factor_1': components[:, 0],
        'pca_factor_2': components[:, 1]
    }
    factor_scores_df = pd.DataFrame(factor_scores_data)
    
    # Save outputs
    loadings_path = ANALYSIS_DIR / "pca_loadings.csv"
    factor_scores_path = ANALYSIS_DIR / "factor_scores.csv"
    
    loadings_df.to_csv(loadings_path, index=True)
    factor_scores_df.to_csv(factor_scores_path, index=False)
    
    logger.log("run_pca_on_metrics", status="success", 
               output_loadings=str(loadings_path), 
               output_scores=str(factor_scores_path))
    
    return loadings_df, factor_scores_df

def run_correlations_with_fd_covariate(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes Spearman/Pearson correlations between metrics and motor scores,
    controlling for Framewise Displacement (FD) using partial correlation logic
    (via residuals or statsmodels).
    For this implementation, we use a simplified approach:
    1. Regress metric ~ FD
    2. Regress motor_score ~ FD
    3. Correlate residuals.
    Returns a DataFrame of correlation results.
    """
    metric_cols = ['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
    required_cols = ['subject_id', 'motor_score', 'fd'] + metric_cols
    
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns for correlation: {missing}")
    
    results = []
    
    from scipy import stats
    
    for metric in metric_cols:
        # Residualize metric against FD
        # y = beta * x + intercept + res
        slope, intercept, r_val, p_val, std_err = stats.linregress(df['fd'], df[metric])
        metric_residuals = df[metric] - (slope * df['fd'] + intercept)
        
        # Residualize motor_score against FD
        slope_m, intercept_m, _, _, _ = stats.linregress(df['fd'], df['motor_score'])
        motor_residuals = df['motor_score'] - (slope_m * df['fd'] + intercept_m)
        
        # Correlate residuals
        corr, p_value = stats.pearsonr(metric_residuals, motor_residuals)
        
        results.append({
            'metric_name': metric,
            'r': corr,
            'p': p_value,
            'covariate': 'fd'
        })
    
    res_df = pd.DataFrame(results)
    corr_path = ANALYSIS_DIR / "correlations.csv"
    res_df.to_csv(corr_path, index=False)
    
    logger.log("run_correlations_with_fd_covariate", status="success", 
               output=str(corr_path), rows=len(res_df))
    
    return res_df

def apply_fdr_correction(correlation_df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies Benjamini-Hochberg FDR correction to p-values.
    Adds columns 'q' (adjusted p-value) and 'significant' (boolean).
    """
    if 'p' not in correlation_df.columns:
        raise ValueError("Input DataFrame must have 'p' column for FDR correction.")
    
    p_vals = correlation_df['p'].values
    _, q_vals, _, _ = multipletests(p_vals, alpha=0.05, method='fdr_bh')
    
    correlation_df = correlation_df.copy()
    correlation_df['q'] = q_vals
    correlation_df['significant'] = q_vals < 0.05
    
    fdr_path = ANALYSIS_DIR / "correlations_fdr.csv"
    correlation_df.to_csv(fdr_path, index=False)
    
    logger.log("apply_fdr_correction", status="success", 
               output=str(fdr_path), significant_count=correlation_df['significant'].sum())
    
    return correlation_df

def generate_full_metrics(base_df: pd.DataFrame, factor_scores_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merges individual metric columns (from T021/T022) with PCA factor scores 
    into a single output DataFrame.
    Output: data/analysis/full_metrics.csv containing all raw metrics AND PCA factors.
    """
    # Ensure base_df has subject_id
    if 'subject_id' not in base_df.columns:
        raise ValueError("Base metrics DataFrame must contain 'subject_id'.")
    
    # Ensure factor_scores_df has subject_id
    if 'subject_id' not in factor_scores_df.columns:
        raise ValueError("Factor scores DataFrame must contain 'subject_id'.")
    
    # Merge on subject_id
    # We keep all columns from base_df and add PCA columns
    merged_df = pd.merge(base_df, factor_scores_df, on='subject_id', how='left')
    
    output_path = ANALYSIS_DIR / "full_metrics.csv"
    merged_df.to_csv(output_path, index=False)
    
    logger.log("generate_full_metrics", status="success", 
               output=str(output_path), rows=len(merged_df))
    
    return merged_df

def main() -> None:
    """
    Main entry point for the analysis pipeline step T023b.
    Executes:
    1. Load aggregated metrics.
    2. Run PCA (generates factor_scores.csv, pca_loadings.csv).
    3. Run correlations with FD covariate.
    4. Apply FDR correction.
    5. Generate full_metrics.csv (T023b primary output).
    """
    logger.log("main", step="T023b", status="started")
    
    try:
        # 1. Load Data
        metrics_df = load_metrics_data()
        
        # 2. Run PCA (T023a dependency)
        # This generates pca_loadings.csv and factor_scores.csv
        loadings_df, factor_scores_df = run_pca_on_metrics(metrics_df)
        
        # 3. Run Correlations (T024 dependency)
        # This generates correlations.csv
        corr_df = run_correlations_with_fd_covariate(metrics_df)
        
        # 4. Apply FDR (T025 dependency)
        corr_df_corrected = apply_fdr_correction(corr_df)
        
        # 5. Generate Full Metrics (T023b primary task)
        # Merge raw metrics with PCA scores
        full_df = generate_full_metrics(metrics_df, factor_scores_df)
        
        logger.log("main", step="T023b", status="completed", 
                   output_file="data/analysis/full_metrics.csv")
        
    except Exception as e:
        logger.log("main", step="T023b", status="failed", error=str(e))
        raise

if __name__ == "__main__":
    main()

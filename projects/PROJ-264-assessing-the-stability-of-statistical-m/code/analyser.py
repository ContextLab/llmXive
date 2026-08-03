import logging
import math
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import pearsonr, spearmanr
from code.config import RESULTS_DIR, CORRELATION_RESULTS_FILE, PERMUTATION_RESULTS_FILE
from code.results_writer import write_correlation_results, write_permutation_results

logger = logging.getLogger(__name__)

def load_raw_evaluations(filepath: Optional[str] = None) -> pd.DataFrame:
    """Load raw evaluation results from CSV."""
    if filepath is None:
        filepath = str(RESULTS_DIR / RAW_EVALUATIONS_FILE)
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Raw evaluations file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    return df

def load_dataset_properties() -> pd.DataFrame:
    """Load dataset properties (n_samples, n_features) from metadata."""
    # In a real implementation, this would load from a specific metadata file
    # constructed during data loading. For now, we assume it's available
    # or derived from the raw evaluations if metadata is stored there.
    # This is a placeholder for the actual implementation which would
    # read from a specific metadata file generated during T005.
    # For this task, we assume the correlation results file exists with
    # dataset properties already joined or we load them separately.
    # Since T019/T021 already produced correlation_results.csv, we assume
    # the properties are embedded or available.
    
    # Actually, for T026, we need to read the raw p-values from the
    # correlation results and permutation results files.
    pass

def calculate_cv(values: np.ndarray) -> float:
    """Calculate coefficient of variation (std/mean)."""
    if len(values) == 0:
        return 0.0
    mean_val = np.mean(values)
    if mean_val == 0:
        return 0.0
    std_val = np.std(values)
    return std_val / mean_val

def aggregate_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate raw evaluations into mean and CV metrics per (dataset, model)."""
    if df.empty:
        return pd.DataFrame()
    
    # Group by dataset_id and model_name
    grouped = df.groupby(['dataset_id', 'model_name'])
    
    results = []
    for (ds_id, model_name), group in grouped:
        acc_mean = group['accuracy'].mean()
        acc_std = group['accuracy'].std()
        acc_cv = acc_std / acc_mean if acc_mean != 0 else 0.0
        
        f1_mean = group['f1_score'].mean()
        f1_std = group['f1_score'].std()
        f1_cv = f1_std / f1_mean if f1_mean != 0 else 0.0
        
        results.append({
            'dataset_id': ds_id,
            'model_name': model_name,
            'mean_accuracy': acc_mean,
            'std_accuracy': acc_std,
            'cv_accuracy': acc_cv,
            'mean_f1': f1_mean,
            'std_f1': f1_std,
            'cv_f1': f1_cv
        })
    
    return pd.DataFrame(results)

def calculate_correlations(metrics_df: pd.DataFrame, properties_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate Pearson and Spearman correlations between CV metrics and dataset properties."""
    # Merge metrics with properties
    merged = metrics_df.merge(properties_df, on='dataset_id', how='inner')
    
    if merged.empty:
        return pd.DataFrame()
    
    results = []
    
    # Properties to correlate with
    properties = ['n_samples', 'n_features']
    metrics = ['cv_accuracy', 'cv_f1']
    
    for prop in properties:
        for metric in metrics:
            if prop not in merged.columns or metric not in merged.columns:
                continue
            
            # Filter out zero-variance cases for correlation
            mask = ~((merged[metric] == 0) | (merged[prop] == 0))
            if mask.sum() < 2:
                continue
            
            x = merged.loc[mask, prop]
            y = merged.loc[mask, metric]
            
            # Pearson correlation
            try:
                pearson_r, pearson_p = pearsonr(x, y)
            except Exception:
                pearson_r, pearson_p = np.nan, np.nan
            
            # Spearman correlation
            try:
                spearman_r, spearman_p = spearmanr(x, y)
            except Exception:
                spearman_r, spearman_p = np.nan, np.nan
            
            results.append({
                'property': prop,
                'metric': metric,
                'pearson_r': pearson_r,
                'pearson_p': pearson_p,
                'spearman_r': spearman_r,
                'spearman_p': spearman_p
            })
    
    return pd.DataFrame(results)

def compute_regression_residuals(metrics_df: pd.DataFrame, properties_df: pd.DataFrame) -> pd.DataFrame:
    """Compute residuals from log-log linear regression of CV vs n_samples and n_features."""
    # Similar to calculate_correlations but with regression residuals
    merged = metrics_df.merge(properties_df, on='dataset_id', how='inner')
    
    if merged.empty:
        return pd.DataFrame()
    
    results = []
    
    for prop in ['n_samples', 'n_features']:
        for metric in ['cv_accuracy', 'cv_f1']:
            if prop not in merged.columns or metric not in merged.columns:
                continue
            
            # Filter zero values for log transformation
            mask = (merged[metric] > 0) & (merged[prop] > 0)
            if mask.sum() < 2:
                continue
            
            x = np.log(merged.loc[mask, prop])
            y = np.log(merged.loc[mask, metric])
            
            # Linear regression
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            
            # Calculate residuals
            predicted = slope * x + intercept
            residuals = y - predicted
            
            results.append({
                'property': prop,
                'metric': metric,
                'slope': slope,
                'intercept': intercept,
                'r_squared': r_value**2,
                'residuals_mean': np.mean(residuals),
                'residuals_std': np.std(residuals)
            })
    
    return pd.DataFrame(results)

def run_correlation_analysis() -> pd.DataFrame:
    """Run full correlation analysis pipeline."""
    # Load data
    raw_df = load_raw_evaluations()
    # For this implementation, we assume dataset properties are available
    # In a real scenario, this would be loaded from a metadata file
    # generated during data loading phase
    properties_df = load_dataset_properties()
    
    # Aggregate metrics
    metrics_df = aggregate_metrics(raw_df)
    
    # Calculate correlations
    corr_df = calculate_correlations(metrics_df, properties_df)
    
    return corr_df

def run_full_permutation_analysis() -> pd.DataFrame:
    """Run permutation tests to compare variance distributions across models."""
    # Load aggregated metrics
    raw_df = load_raw_evaluations()
    metrics_df = aggregate_metrics(raw_df)
    
    if metrics_df.empty:
        return pd.DataFrame()
    
    # We need to compare variance distributions between model pairs
    # For each dataset, we have accuracy scores from CV folds
    # We'll compare the variances of accuracy scores between models
    
    # Group by dataset_id
    datasets = raw_df['dataset_id'].unique()
    model_pairs = [('LogisticRegression', 'RandomForest'), 
                   ('LogisticRegression', 'SVM'), 
                   ('RandomForest', 'SVM')]
    
    results = []
    
    for ds_id in datasets:
        ds_data = raw_df[raw_df['dataset_id'] == ds_id]
        
        for model_a, model_b in model_pairs:
            acc_a = ds_data[ds_data['model_name'] == model_a]['accuracy'].values
            acc_b = ds_data[ds_data['model_name'] == model_b]['accuracy'].values
            
            if len(acc_a) < 2 or len(acc_b) < 2:
                continue
            
            # Calculate variances
            var_a = np.var(acc_a)
            var_b = np.var(acc_b)
            
            # Test statistic: absolute difference of variances
            observed_stat = abs(var_a - var_b)
            
            # Permutation test
            combined = np.concatenate([acc_a, acc_b])
            n_a = len(acc_a)
            n_permutations = 1000
            
            perm_stats = []
            for _ in range(n_permutations):
                np.random.shuffle(combined)
                perm_a = combined[:n_a]
                perm_b = combined[n_a:]
                perm_var_a = np.var(perm_a)
                perm_var_b = np.var(perm_b)
                perm_stat = abs(perm_var_a - perm_var_b)
                perm_stats.append(perm_stat)
            
            # Calculate p-value
            p_value = (np.sum(perm_stats >= observed_stat) + 1) / (n_permutations + 1)
            
            results.append({
                'dataset_id': ds_id,
                'model_a': model_a,
                'model_b': model_b,
                'var_a': var_a,
                'var_b': var_b,
                'observed_stat': observed_stat,
                'p_value': p_value
            })
    
    return pd.DataFrame(results)

def apply_bonferroni_correction(p_values: List[float]) -> List[float]:
    """Apply Bonferroni correction to a list of p-values."""
    n = len(p_values)
    if n == 0:
        return []
    
    # Bonferroni: multiply each p-value by n, cap at 1.0
    adjusted = [min(p * n, 1.0) for p in p_values]
    return adjusted

def apply_bonferroni_correction_dataframe(df: pd.DataFrame, p_col: str) -> pd.DataFrame:
    """Apply Bonferroni correction to a DataFrame column of p-values."""
    if df.empty or p_col not in df.columns:
        return df
    
    p_values = df[p_col].dropna().tolist()
    if len(p_values) == 0:
        return df
    
    adjusted = apply_bonferroni_correction(p_values)
    
    # Create a mapping from original p-values to adjusted values
    # Handle duplicate p-values by assigning the same adjusted value
    p_to_adj = {}
    for i, p in enumerate(p_values):
        p_to_adj[p] = adjusted[i]
    
    df[f'{p_col}_adj'] = df[p_col].map(p_to_adj)
    return df

def run_bonferroni_correction() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Apply Bonferroni correction globally across ALL hypothesis tests.
    
    This function:
    1. Loads correlation results (from T019/T021)
    2. Loads permutation results (from T025)
    3. Collects ALL p-values from both sources
    4. Applies Bonferroni correction across the entire family
    5. Writes adjusted results back to the respective files
    
    Returns:
        Tuple of (adjusted_correlation_df, adjusted_permutation_df)
    """
    # Load correlation results
    corr_file = RESULTS_DIR / CORRELATION_RESULTS_FILE
    if not corr_file.exists():
        logger.warning(f"Correlation results file not found: {corr_file}")
        corr_df = pd.DataFrame()
    else:
        corr_df = pd.read_csv(corr_file)
    
    # Load permutation results
    perm_file = RESULTS_DIR / PERMUTATION_RESULTS_FILE
    if not perm_file.exists():
        logger.warning(f"Permutation results file not found: {perm_file}")
        perm_df = pd.DataFrame()
    else:
        perm_df = pd.read_csv(perm_file)
    
    # Collect all p-values from both sources
    all_p_values = []
    p_sources = []  # Track which source each p-value came from
    
    if not corr_df.empty and 'pearson_p' in corr_df.columns:
        for p in corr_df['pearson_p'].dropna():
            all_p_values.append(p)
            p_sources.append('correlation_pearson')
    
    if not corr_df.empty and 'spearman_p' in corr_df.columns:
        for p in corr_df['spearman_p'].dropna():
            all_p_values.append(p)
            p_sources.append('correlation_spearman')
    
    if not perm_df.empty and 'p_value' in perm_df.columns:
        for p in perm_df['p_value'].dropna():
            all_p_values.append(p)
            p_sources.append('permutation')
    
    if len(all_p_values) == 0:
        logger.warning("No p-values found to correct.")
        return corr_df, perm_df
    
    logger.info(f"Applying Bonferroni correction to {len(all_p_values)} hypothesis tests.")
    
    # Apply Bonferroni correction across the entire family
    adjusted_p_values = apply_bonferroni_correction(all_p_values)
    
    # Create mapping for correlation results
    if not corr_df.empty and 'pearson_p' in corr_df.columns:
        corr_p_values = corr_df['pearson_p'].dropna().tolist()
        if len(corr_p_values) > 0:
            start_idx = 0
            corr_adj_values = adjusted_p_values[start_idx:start_idx+len(corr_p_values)]
            corr_df['pearson_p_adj'] = corr_df['pearson_p'].map(dict(zip(corr_p_values, corr_adj_values)))
            corr_df['pearson_p_adj'] = corr_df['pearson_p_adj'].fillna(1.0)  # Handle NaNs
    
    if not corr_df.empty and 'spearman_p' in corr_df.columns:
        spearman_p_values = corr_df['spearman_p'].dropna().tolist()
        if len(spearman_p_values) > 0:
            start_idx = len(corr_p_values) if 'pearson_p' in corr_df.columns else 0
            spearman_adj_values = adjusted_p_values[start_idx:start_idx+len(spearman_p_values)]
            corr_df['spearman_p_adj'] = corr_df['spearman_p'].map(dict(zip(spearman_p_values, spearman_adj_values)))
            corr_df['spearman_p_adj'] = corr_df['spearman_p_adj'].fillna(1.0)
    
    # Create mapping for permutation results
    if not perm_df.empty and 'p_value' in perm_df.columns:
        perm_p_values = perm_df['p_value'].dropna().tolist()
        if len(perm_p_values) > 0:
            start_idx = len(corr_p_values) + len(spearman_p_values) if 'pearson_p' in corr_df.columns else 0
            if 'spearman_p' in corr_df.columns:
                start_idx += len(spearman_p_values)
            perm_adj_values = adjusted_p_values[start_idx:start_idx+len(perm_p_values)]
            perm_df['p_value_adj'] = perm_df['p_value'].map(dict(zip(perm_p_values, perm_adj_values)))
            perm_df['p_value_adj'] = perm_df['p_value_adj'].fillna(1.0)
    
    # Write adjusted results back to files
    if not corr_df.empty:
        write_correlation_results(corr_df)
        logger.info("Updated correlation results with Bonferroni-adjusted p-values.")
    
    if not perm_df.empty:
        write_permutation_results(perm_df)
        logger.info("Updated permutation results with Bonferroni-adjusted p-values.")
    
    return corr_df, perm_df

def main():
    """Main entry point for analysis."""
    setup_logging()
    logger.info("Starting statistical analysis pipeline.")
    
    # Run correlation analysis
    corr_df = run_correlation_analysis()
    if not corr_df.empty:
        write_correlation_results(corr_df)
        logger.info(f"Correlation analysis complete. {len(corr_df)} results written.")
    
    # Run permutation analysis
    perm_df = run_full_permutation_analysis()
    if not perm_df.empty:
        write_permutation_results(perm_df)
        logger.info(f"Permutation analysis complete. {len(perm_df)} results written.")
    
    # Apply Bonferroni correction across all tests
    logger.info("Applying Bonferroni correction to all hypothesis tests...")
    corr_df_adj, perm_df_adj = run_bonferroni_correction()
    
    logger.info("Analysis pipeline complete.")

if __name__ == "__main__":
    main()

import os
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.decomposition import PCA
from config import get_config
from logging_config import setup_logging, get_logger

# Initialize logger
setup_logging()
logger = get_logger(__name__)

def calculate_batch_size(total_memory_gb: float = 7.0) -> int:
    """
    Calculate dynamic batch size based on memory constraints.
    Assumes a rough memory footprint per subject matrix (400x400 float64).
    400*400*8 bytes ≈ 1.28 MB per matrix.
    """
    # Reserve 1GB for OS and overhead, leave rest for data
    available_gb = total_memory_gb - 1.0
    if available_gb <= 0:
        return 1
    
    # Estimate max subjects that fit
    # 1 subject ~ 1.28 MB. Let's be conservative and say 50MB per subject for overhead.
    bytes_per_subject = 50 * 1024 * 1024 
    available_bytes = available_gb * 1024 * 1024 * 1024
    batch_size = int(available_bytes / bytes_per_subject)
    return max(1, batch_size)

def run_correlation_analysis(metrics_df: pd.DataFrame, target_col: str = 'motor_score', covariate_col: str = 'fd') -> pd.DataFrame:
    """
    Run Spearman/Pearson correlations with covariate control.
    Input: DataFrame with metric columns and subject info.
    Output: DataFrame of correlation results (r, p, q, significant).
    """
    if metrics_df.empty:
        logger.warning("Input metrics DataFrame is empty.")
        return pd.DataFrame()

    metric_cols = [c for c in metrics_df.columns if c not in ['subject_id', target_col, covariate_col, 'pca_factor_1', 'pca_factor_2']]
    
    results = []
    
    for metric in metric_cols:
        if metric not in metrics_df.columns:
            continue
        
        # Filter out NaNs
        valid_data = metrics_df[[metric, target_col, covariate_col]].dropna()
        if len(valid_data) < 5:
            logger.warning(f"Not enough data for {metric}, skipping.")
            continue
        
        x = valid_data[metric].values
        y = valid_data[target_col].values
        
        # Partial correlation logic (simplified: regress out covariate from both, then correlate)
        # Using scipy.stats for partial correlation is not direct, so we do linear regression residuals
        try:
            from scipy import stats
            
            # Regress metric on covariate
            model_x = stats.linregress(valid_data[covariate_col], x)
            residuals_x = x - (model_x.slope * valid_data[covariate_col].values + model_x.intercept)
            
            # Regress target on covariate
            model_y = stats.linregress(valid_data[covariate_col], y)
            residuals_y = y - (model_y.slope * valid_data[covariate_col].values + model_y.intercept)
            
            r, p_value = stats.spearmanr(residuals_x, residuals_y)
            
            results.append({
                'metric_name': metric,
                'r': r,
                'p': p_value,
                'q': np.nan, # To be filled by FDR
                'significant': False,
                'covariate_controlled': True
            })
        except Exception as e:
            logger.error(f"Error calculating correlation for {metric}: {e}")
            continue
    
    return pd.DataFrame(results)

def apply_fdr_correction(correlation_results: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
    """
    Apply Benjamini-Hochberg FDR correction to p-values.
    """
    if correlation_results.empty:
        return correlation_results
    
    df = correlation_results.copy()
    df = df.sort_values('p')
    df['rank'] = range(1, len(df) + 1)
    m = len(df)
    
    # BH procedure
    df['threshold'] = (df['rank'] / m) * alpha
    df['significant'] = df['p'] <= df['threshold']
    
    # Calculate q-values (adjusted p-values)
    # Simple approximation: q = p * m / rank
    df['q'] = df['p'] * m / df['rank']
    df['q'] = df['q'].clip(upper=1.0)
    
    # Ensure monotonicity (optional but good practice)
    # Reverse cumulative min
    df['q'] = df['q'].iloc[::-1].cummin().iloc[::-1]
    
    return df

def log_correlation_threshold(correlation_results: pd.DataFrame, threshold: float = 0.3):
    """
    Log significant correlations above a certain magnitude.
    """
    significant = correlation_results[correlation_results['significant']]
    strong = significant[significant['r'].abs() > threshold]
    
    if not strong.empty:
        logger.info(f"Found {len(strong)} strong significant correlations (|r| > {threshold}):")
        for _, row in strong.iterrows():
            logger.info(f"  {row['metric_name']}: r={row['r']:.3f}, p={row['p']:.3f}, q={row['q']:.3f}")
    else:
        logger.info(f"No strong significant correlations found (|r| > {threshold}).")

def merge_metrics_and_pca_scores(metrics_df: pd.DataFrame, pca_scores_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge individual metric columns (raw metrics) with PCA factor scores.
    Ensures FR-005 (FDR on individual metrics) and FR-004 (report generation) have access to all data.
    
    Args:
        metrics_df: DataFrame containing subject_id and raw metric columns (e.g., modularity, global_efficiency, etc.)
        pca_scores_df: DataFrame containing subject_id and PCA factor columns (e.g., pca_factor_1, pca_factor_2)
    
    Returns:
        Combined DataFrame with all columns.
    """
    if metrics_df is None or metrics_df.empty:
        logger.warning("Input metrics DataFrame is empty or None.")
        return pd.DataFrame()
    
    if pca_scores_df is not None and not pca_scores_df.empty:
        # Merge on subject_id. 'how'='left' ensures all metrics are kept even if PCA failed for some.
        merged_df = pd.merge(metrics_df, pca_scores_df, on='subject_id', how='left')
        logger.info(f"Merged {len(metrics_df)} metric rows with PCA scores. Result shape: {merged_df.shape}")
    else:
        logger.warning("PCA scores DataFrame is empty or None. Returning raw metrics only.")
        merged_df = metrics_df.copy()
    
    return merged_df

def main():
    """
    Main entry point for T023b: File Output & Metric Preservation.
    Loads raw metrics and PCA scores, merges them, and writes to data/analysis/full_metrics.csv.
    """
    logger.info("Starting T023b: Merging metrics and PCA scores.")
    
    config = get_config()
    data_dir = Path(config.get('DATA_DIR', 'data'))
    analysis_dir = data_dir / 'analysis'
    analysis_dir.mkdir(parents=True, exist_ok=True)
    
    # Define paths
    # Assuming T021/T022 output is aggregated in data/analysis/aggregated_metrics.csv or similar
    # Assuming T023a output is data/analysis/factor_scores.csv
    metrics_path = analysis_dir / 'aggregated_metrics.csv'
    pca_scores_path = analysis_dir / 'factor_scores.csv'
    output_path = analysis_dir / 'full_metrics.csv'
    
    # Load metrics
    if metrics_path.exists():
        metrics_df = pd.read_csv(metrics_path)
        logger.info(f"Loaded metrics from {metrics_path}. Shape: {metrics_df.shape}")
    else:
        logger.error(f"Metrics file not found at {metrics_path}. Cannot proceed with merge.")
        # Attempt to load from other possible locations if standard path fails, 
        # but strictly following spec: T021/T022 should produce this.
        # If not found, we might need to look for 'graph_metrics.csv' or similar if naming differs.
        # For now, fail loudly as per constraint 7.
        raise FileNotFoundError(f"Required metrics file {metrics_path} not found.")
    
    # Load PCA scores
    pca_scores_df = None
    if pca_scores_path.exists():
        pca_scores_df = pd.read_csv(pca_scores_path)
        logger.info(f"Loaded PCA scores from {pca_scores_path}. Shape: {pca_scores_df.shape}")
    else:
        logger.warning(f"PCA scores file not found at {pca_scores_path}. Proceeding with metrics only.")
    
    # Merge
    final_df = merge_metrics_and_pca_scores(metrics_df, pca_scores_df)
    
    if final_df.empty:
        logger.error("Final merged DataFrame is empty. Aborting write.")
        return
    
    # Ensure subject_id is first column for readability
    cols = ['subject_id'] + [c for c in final_df.columns if c != 'subject_id']
    final_df = final_df[cols]
    
    # Write output
    final_df.to_csv(output_path, index=False)
    logger.info(f"Successfully wrote full_metrics.csv to {output_path}")
    
    # Verify file exists and has content
    if output_path.exists() and output_path.stat().st_size > 0:
        logger.info("Verification: Output file exists and is non-empty.")
    else:
        logger.error("Verification failed: Output file missing or empty.")

if __name__ == "__main__":
    main()
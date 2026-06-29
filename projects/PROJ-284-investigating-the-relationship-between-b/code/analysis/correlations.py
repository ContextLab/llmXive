import os
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.decomposition import PCA
from scipy import stats

from config import get_config
from logging_config import setup_logging, get_logger
from models import CorrelationResult

# Initialize logger
logger = get_logger("correlations")

def apply_fdr_correction(p_values, alpha=0.05):
    """
    Apply Benjamini-Hochberg FDR correction to a list of p-values.
    
    Args:
        p_values: List or array of p-values
        alpha: Significance threshold
        
    Returns:
        List of booleans indicating significance after FDR correction
    """
    p_values = np.array(p_values)
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]
    
    # Calculate critical values
    critical_values = (np.arange(1, n + 1) / n) * alpha
    
    # Find the largest k such that p_(k) <= critical_value_(k)
    significant = np.zeros(n, dtype=bool)
    for i in range(n - 1, -1, -1):
        if sorted_p[i] <= critical_values[i]:
            significant[sorted_indices[:i+1]] = True
            break
            
    return significant.tolist()

def calculate_batch_size(total_rows, memory_limit_gb=7.0):
    """
    Calculate optimal batch size for matrix computation based on memory constraints.
    
    Assumes:
    - Each row in the metrics DataFrame takes ~1KB of RAM for processing overhead
    - Additional overhead for correlation matrices and intermediate calculations
    
    Args:
        total_rows: Total number of subjects to process
        memory_limit_gb: Available memory in GB (default 7GB as per config)
        
    Returns:
        int: Optimal batch size to process
    """
    # Conservative estimate: 1KB per row for basic data + 2KB for intermediate structures
    bytes_per_row = 3072  # 3KB
    
    # Reserve 20% for Python interpreter overhead and other processes
    usable_memory_bytes = (memory_limit_gb * 1024**3) * 0.8
    
    # Calculate max rows that fit in memory
    max_rows = int(usable_memory_bytes / bytes_per_row)
    
    # Ensure at least batch of 10 if data is small, but don't exceed total
    batch_size = min(max(10, max_rows), total_rows)
    
    logger.info(f"Calculated batch size: {batch_size} (total rows: {total_rows}, memory limit: {memory_limit_gb}GB)")
    return batch_size

def run_correlation_analysis(metrics_df, target_column, covariate_column=None):
    """
    Run correlation analysis between network metrics and behavioral scores.
    
    Args:
        metrics_df: DataFrame containing network metrics and behavioral data
        target_column: Name of the column to correlate against (e.g., 'motor_score')
        covariate_column: Optional column name for covariate control (e.g., 'fd')
        
    Returns:
        List of CorrelationResult objects
    """
    results = []
    config = get_config()
    memory_limit = config.get('MEMORY_LIMIT', 7.0)
    
    # Identify metric columns (exclude non-metric columns)
    exclude_cols = ['subject_id', 'age', 'sex', 'fd', target_column]
    if covariate_column:
        exclude_cols.append(covariate_column)
        
    metric_cols = [col for col in metrics_df.columns if col not in exclude_cols]
    
    if not metric_cols:
        logger.warning("No metric columns found for correlation analysis")
        return results
    
    # Calculate optimal batch size
    total_rows = len(metrics_df)
    batch_size = calculate_batch_size(total_rows, memory_limit)
    
    logger.info(f"Starting correlation analysis with batch size {batch_size}")
    
    # Process in batches if necessary
    for start_idx in range(0, total_rows, batch_size):
        end_idx = min(start_idx + batch_size, total_rows)
        batch_df = metrics_df.iloc[start_idx:end_idx].copy()
        
        logger.info(f"Processing batch {start_idx//batch_size + 1}: subjects {start_idx} to {end_idx-1}")
        
        for metric in metric_cols:
            if metric not in batch_df.columns:
                continue
                
            x = batch_df[metric].dropna()
            y = batch_df[target_column].loc[x.index].dropna()
            
            # Re-align after dropna
            valid_indices = x.index.intersection(y.index)
            x = x.loc[valid_indices]
            y = y.loc[valid_indices]
            
            if len(x) < 5:  # Minimum sample size for correlation
                continue
                
            # Calculate correlation
            r, p_value = stats.spearmanr(x, y)
            
            # Control for covariate if provided
            q_value = p_value
            covariate_controlled = False
            
            if covariate_column and covariate_column in batch_df.columns:
                z = batch_df[covariate_column].loc[valid_indices].dropna()
                valid_indices = valid_indices.intersection(z.index)
                if len(valid_indices) >= 5:
                    x = x.loc[valid_indices]
                    y = y.loc[valid_indices]
                    z = z.loc[valid_indices]
                    
                    # Partial correlation
                    r_xy = np.corrcoef(x, y)[0, 1]
                    r_xz = np.corrcoef(x, z)[0, 1]
                    r_yz = np.corrcoef(y, z)[0, 1]
                    
                    if abs(1 - r_xz**2 - r_yz**2) > 1e-10:
                        r_partial = (r_xy - r_xz * r_yz) / np.sqrt((1 - r_xz**2) * (1 - r_yz**2))
                        # Approximate p-value for partial correlation
                        t_stat = r_partial * np.sqrt((len(x) - 3) / (1 - r_partial**2))
                        q_value = 2 * (1 - stats.t.cdf(abs(t_stat), len(x) - 3))
                        covariate_controlled = True
                    
            results.append(CorrelationResult(
                metric_name=metric,
                r=r if not np.isnan(r) else 0.0,
                p=p_value if not np.isnan(p_value) else 1.0,
                q=q_value if not np.isnan(q_value) else 1.0,
                significant=False,  # Will be updated after FDR
                covariate_controlled=covariate_controlled
            ))
    
    # Apply FDR correction to all results
    if results:
        p_values = [r.p for r in results]
        significant_flags = apply_fdr_correction(p_values)
        for i, result in enumerate(results):
            result.significant = significant_flags[i]
    
    return results

def log_correlation_threshold(results, threshold=0.3):
    """
    Log correlation results that exceed the specified threshold.
    
    Args:
        results: List of CorrelationResult objects
        threshold: Absolute correlation threshold
    """
    significant_results = [r for r in results if r.significant and abs(r.r) > threshold]
    
    logger.info(f"Found {len(significant_results)} significant correlations with |r| > {threshold}")
    
    for r in significant_results:
        logger.info(f"  {r.metric_name}: r={r.r:.3f}, p={r.p:.4f}, q={r.q:.4f}, covariate_controlled={r.covariate_controlled}")
    
    return significant_results

def main():
    """
    Main entry point for correlation analysis.
    
    Reads processed metrics data, runs correlation analysis,
    applies FDR correction, and logs results.
    """
    setup_logging()
    
    # Load data
    data_path = Path("data/analysis/full_metrics.csv")
    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}")
        return
    
    metrics_df = pd.read_csv(data_path)
    
    # Run analysis
    results = run_correlation_analysis(
        metrics_df, 
        target_column='motor_score',
        covariate_column='fd'
    )
    
    # Log significant results
    log_correlation_threshold(results)
    
    # Save results
    output_path = Path("data/analysis/correlation_results.csv")
    output_df = pd.DataFrame([
        {
            'metric_name': r.metric_name,
            'r': r.r,
            'p': r.p,
            'q': r.q,
            'significant': r.significant,
            'covariate_controlled': r.covariate_controlled
        }
        for r in results
    ])
    output_df.to_csv(output_path, index=False)
    
    logger.info(f"Correlation results saved to {output_path}")

if __name__ == "__main__":
    main()
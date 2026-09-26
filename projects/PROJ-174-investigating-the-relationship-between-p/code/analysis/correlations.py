import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import scipy.stats as stats

# Configure logging for this module
logger = logging.getLogger(__name__)

def load_processed_data(input_path: Union[str, Path]) -> pd.DataFrame:
    """
    Load the preprocessed data from a CSV file.
    Expects columns: subject_id, trial_id, timestamp, pupil_diameter, 
                    search_time, target_salience, fixation_count, status
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Processed data file not found: {path}")
    
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} rows from {path}")
    return df

def extract_pupil_metrics(df: pd.DataFrame) -> Dict[str, pd.Series]:
    """
    Extract different pupil diameter metrics from the data.
    Returns:
        Dict with keys 'peak', 'mean', 'quantized' containing Series aligned with input.
    """
    metrics = {}
    
    # Peak pupil diameter per trial (assuming data is already aggregated or we take max per trial)
    # If data is raw time-series, we need to group by trial first. 
    # Assuming input 'df' is trial-wise or we compute max per trial if raw.
    # Given the context of US1, we assume 'df' might be trial-level aggregates or raw.
    # If raw: group by trial_id to get peak/mean. If already trial-level, just use 'pupil_diameter'.
    
    # Check if we have trial-level aggregation or raw data
    if 'trial_id' in df.columns and len(df) > df['trial_id'].nunique():
        # Raw data: aggregate by trial
        grouped = df.groupby('trial_id')
        metrics['peak'] = grouped['pupil_diameter'].max()
        metrics['mean'] = grouped['pupil_diameter'].mean()
        # Quantized: 0=low, 1=mid, 2=high based on global quartiles
        q1, q3 = df['pupil_diameter'].quantile([0.33, 0.66])
        def quantize(x):
            if x < q1: return 0
            elif x < q3: return 1
            else: return 2
        metrics['quantized'] = grouped['pupil_diameter'].mean().apply(quantize)
    else:
        # Already aggregated or single row per trial
        # We assume 'pupil_diameter' is the metric of interest for the trial
        metrics['peak'] = df['pupil_diameter']
        metrics['mean'] = df['pupil_diameter']
        q1, q3 = df['pupil_diameter'].quantile([0.33, 0.66])
        metrics['quantized'] = df['pupil_diameter'].apply(lambda x: 0 if x < q1 else (1 if x < q3 else 2))
        
    # Ensure index alignment for downstream correlation
    return metrics

def calculate_pearson_correlation(x: pd.Series, y: pd.Series) -> Tuple[float, float]:
    """
    Calculate Pearson correlation coefficient and p-value.
    Handles NaNs by dropping them pairwise.
    Returns:
        Tuple (r, p_value)
    """
    # Drop NaNs
    valid = ~(x.isna() | y.isna())
    if valid.sum() < 3:
        return np.nan, np.nan
    
    r, p = stats.pearsonr(x[valid], y[valid])
    return r, p

def benjamini_hochberg_fdr(p_values: List[float]) -> List[float]:
    """
    Apply Benjamini-Hochberg FDR correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values.
        
    Returns:
        List of adjusted p-values (q-values).
    """
    p_values = np.array(p_values)
    if len(p_values) == 0:
        return []
    
    # Filter out NaNs for calculation, but keep track of original indices
    mask = ~np.isnan(p_values)
    sorted_indices = np.argsort(p_values[mask])
    sorted_p = p_values[mask][sorted_indices]
    n = len(sorted_p)
    
    # Calculate BH critical values
    # p_adj[i] = p[i] * n / (rank[i])
    # But we need to ensure monotonicity from the bottom up
    ranks = np.arange(1, n + 1)
    adjusted = sorted_p * n / ranks
    
    # Ensure monotonicity (cumulative min from the end)
    for i in range(n - 2, -1, -1):
        adjusted[i] = min(adjusted[i], adjusted[i+1])
        
    # Cap at 1.0
    adjusted = np.clip(adjusted, 0, 1.0)
    
    # Map back to original order
    result = np.full_like(p_values, np.nan, dtype=float)
    result[mask][sorted_indices] = adjusted
    
    return result.tolist()

def compute_correlations(df: pd.DataFrame, metrics: Dict[str, pd.Series]) -> pd.DataFrame:
    """
    Compute correlations between pupil metrics and load proxies.
    Proxies: search_time, target_salience, fixation_count.
    
    Returns a DataFrame with columns:
    metric, proxy, r, p_raw, p_adj
    """
    proxies = ['search_time', 'target_salience', 'fixation_count']
    results = []
    
    # Filter out rows where proxies are missing or 'UNFULFILLABLE'
    # We assume 'status' column exists from T015
    valid_mask = (df['status'] != 'UNFULFILLABLE') | (~df['status'].notna())
    # Actually, we should only correlate if the proxy itself is valid numeric
    # Let's iterate and dropna inside the correlation function, but filter globally first
    
    valid_df = df.dropna(subset=proxies + list(metrics.keys()))
    
    if len(valid_df) == 0:
        logger.warning("No valid data points for correlation after dropping NaNs.")
        return pd.DataFrame(columns=['metric', 'proxy', 'r', 'p_raw', 'p_adj'])
    
    all_p_values = []
    correlation_data = []
    
    for metric_name, metric_series in metrics.items():
        # Align metric series with valid_df index if necessary
        # Assuming metric_series index matches df index
        m_series = metric_series.reindex(valid_df.index)
        
        for proxy in proxies:
            p_series = valid_df[proxy]
            
            r, p_raw = calculate_pearson_correlation(m_series, p_series)
            
            if not np.isnan(r):
                correlation_data.append({
                    'metric': metric_name,
                    'proxy': proxy,
                    'r': r,
                    'p_raw': p_raw
                })
                all_p_values.append(p_raw)
            else:
                correlation_data.append({
                    'metric': metric_name,
                    'proxy': proxy,
                    'r': np.nan,
                    'p_raw': np.nan
                })
                all_p_values.append(np.nan)
    
    if not all_p_values or not any(not np.isnan(p) for p in all_p_values):
        logger.warning("No valid p-values to adjust.")
        adjusted_p = [np.nan] * len(correlation_data)
    else:
        adjusted_p = benjamini_hochberg_fdr(all_p_values)
    
    for i, row in enumerate(correlation_data):
        row['p_adj'] = adjusted_p[i]
        
    return pd.DataFrame(correlation_data)

def save_results(df: pd.DataFrame, output_path: Union[str, Path]):
    """
    Save the correlation results to a CSV file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logger.info(f"Saved correlation results to {path}")

def main():
    """
    Main entry point for the correlation analysis pipeline.
    Reads from data/processed/ (or configured path) and writes to results/correlations.csv
    """
    # Setup paths
    # Assuming processed data is in data/processed/ based on T013/T014/T015 flow
    # The task description says output to results/correlations.csv
    input_dir = Path("data/processed")
    output_file = Path("results/correlations.csv")
    
    # Check for config to override paths if needed
    # (Simplified for this task: hardcoded paths as per spec)
    
    if not input_dir.exists():
        logger.error(f"Input directory {input_dir} does not exist.")
        sys.exit(1)
    
    # Find processed files (assuming single consolidated file or multiple subjects)
    # For simplicity, assume a single file 'processed_data.csv' or similar.
    # In a real pipeline, we might aggregate all subjects first.
    # Let's assume T015 produced a single file 'data/processed/trial_data.csv'
    input_file = input_dir / "trial_data.csv"
    if not input_file.exists():
        # Fallback: look for any csv
        csv_files = list(input_dir.glob("*.csv"))
        if not csv_files:
            logger.error("No processed data files found in data/processed/")
            sys.exit(1)
        input_file = csv_files[0]
    
    logger.info(f"Processing file: {input_file}")
    df = load_processed_data(input_file)
    
    metrics = extract_pupil_metrics(df)
    results_df = compute_correlations(df, metrics)
    
    save_results(results_df, output_file)
    
    print(f"Correlation analysis complete. Results saved to {output_file}")
    return results_df

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
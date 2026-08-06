import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('code/logs/analysis.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_processed_data(input_path: str) -> pd.DataFrame:
    """
    Load processed data from CSV.
    Expects columns: subject_id, trial_id, pupil_mean, pupil_peak, pupil_quantile, 
                    search_time, fixation_count, target_salience, status
    """
    logger.info(f"Loading processed data from {input_path}")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Processed data file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Filter out rows marked as UNFULFILLABLE
    valid_mask = df['status'] != 'UNFULFILLABLE'
    df_valid = df[valid_mask].copy()
    
    if len(df_valid) == 0:
        raise ValueError("No valid data rows found after filtering UNFULFILLABLE entries.")
    
    logger.info(f"Loaded {len(df_valid)} valid rows out of {len(df)} total")
    return df_valid

def extract_pupil_metrics(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Extract pupil metric arrays from dataframe.
    Returns: (pupil_mean, pupil_peak, pupil_quantile)
    """
    # Handle potential missing columns gracefully
    mean_col = 'pupil_mean' if 'pupil_mean' in df.columns else None
    peak_col = 'pupil_peak' if 'pupil_peak' in df.columns else None
    quantile_col = 'pupil_quantile' if 'pupil_quantile' in df.columns else None
    
    metrics = []
    if mean_col:
        metrics.append(df[mean_col].dropna().values)
    if peak_col:
        metrics.append(df[peak_col].dropna().values)
    if quantile_col:
        metrics.append(df[quantile_col].dropna().values)
        
    if not metrics:
        raise ValueError("No pupil metric columns found in dataframe.")
    
    # Return the first available metric for now, or combine if needed
    # For this implementation, we assume the first valid column is the primary metric
    return metrics[0], None, None

def calculate_pearson_correlation(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    """
    Calculate Pearson correlation coefficient and p-value.
    Returns: (correlation_coefficient, p_value)
    """
    if len(x) != len(y) or len(x) < 3:
        return np.nan, np.nan
    
    # Remove NaNs
    mask = ~(np.isnan(x) | np.isnan(y))
    x_clean = x[mask]
    y_clean = y[mask]
    
    if len(x_clean) < 3:
        return np.nan, np.nan
    
    correlation, p_value = np.corrcoef(x_clean, y_clean)[0, 1], 0.0
    
    # Calculate p-value for Pearson correlation
    # Using t-distribution: t = r * sqrt((n-2) / (1-r^2))
    n = len(x_clean)
    r = correlation
    if abs(r) >= 1.0:
        p_value = 0.0
    else:
        t_stat = r * np.sqrt((n - 2) / (1 - r**2))
        # Two-tailed p-value
        from scipy import stats
        p_value = 2 * (1 - stats.t.cdf(abs(t_stat), n - 2))
        
    return correlation, p_value

def benjamini_hochberg_fdr(p_values: List[float]) -> List[float]:
    """
    Apply Benjamini-Hochberg FDR correction to a list of p-values.
    Returns: List of adjusted p-values (q-values)
    """
    if not p_values:
        return []
    
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p_values = np.array([p_values[i] for i in sorted_indices])
    
    # Calculate BH critical values
    ranks = np.arange(1, n + 1)
    bh_thresholds = (ranks / n) * 0.05  # alpha = 0.05
    
    # Adjust p-values
    adjusted_p_values = np.zeros(n)
    cumulative_min = 1.0
    
    for i in range(n - 1, -1, -1):
        cumulative_min = min(cumulative_min, sorted_p_values[i] * (n / (i + 1)))
        adjusted_p_values[i] = min(cumulative_min, 1.0)
    
    # Restore original order
    result = np.zeros(n)
    result[sorted_indices] = adjusted_p_values
    
    return result.tolist()

def compute_correlations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute Pearson correlations between pupil metrics and load proxies.
    Returns DataFrame with correlation results.
    """
    results = []
    
    # Define proxy variables to test against
    proxy_vars = []
    if 'search_time' in df.columns:
        proxy_vars.append(('search_time', df['search_time'].values))
    if 'fixation_count' in df.columns:
        proxy_vars.append(('fixation_count', df['fixation_count'].values))
    if 'target_salience' in df.columns:
        proxy_vars.append(('target_salience', df['target_salience'].values))
    
    # Define pupil metrics
    pupil_metrics = []
    if 'pupil_mean' in df.columns:
        pupil_metrics.append(('pupil_mean', df['pupil_mean'].values))
    if 'pupil_peak' in df.columns:
        pupil_metrics.append(('pupil_peak', df['pupil_peak'].values))
    if 'pupil_quantile' in df.columns:
        pupil_metrics.append(('pupil_quantile', df['pupil_quantile'].values))
    
    if not proxy_vars or not pupil_metrics:
        logger.warning("Missing required columns for correlation analysis.")
        return pd.DataFrame()
    
    all_p_values = []
    correlation_records = []
    
    # Compute correlations
    for pupil_name, pupil_vals in pupil_metrics:
        for proxy_name, proxy_vals in proxy_vars:
            r, p = calculate_pearson_correlation(pupil_vals, proxy_vals)
            
            if not np.isnan(r):
                correlation_records.append({
                    'pupil_metric': pupil_name,
                    'proxy_variable': proxy_name,
                    'correlation': r,
                    'p_value_raw': p,
                    'n_samples': len(pupil_vals)
                })
                all_p_values.append(p)
    
    if not all_p_values:
        logger.warning("No valid correlations computed.")
        return pd.DataFrame()
    
    # Apply FDR correction
    adjusted_p_values = benjamini_hochberg_fdr(all_p_values)
    
    # Update results with adjusted p-values
    for i, record in enumerate(correlation_records):
        record['p_value_fdr'] = adjusted_p_values[i]
    
    return pd.DataFrame(correlation_records)

def save_results(df_results: pd.DataFrame, output_path: str):
    """
    Save correlation results to CSV.
    """
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    df_results.to_csv(output_path, index=False)
    logger.info(f"Saved correlation results to {output_path}")

def main():
    """
    Main entry point for correlation analysis pipeline.
    """
    # Configuration
    input_file = 'data/processed/combined_features.csv'
    output_file = 'results/correlations.csv'
    
    # Check if input file exists
    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        logger.error("Please ensure preprocessing pipeline has run successfully.")
        sys.exit(1)
    
    try:
        # Load data
        df = load_processed_data(input_file)
        
        # Compute correlations
        results_df = compute_correlations(df)
        
        if results_df.empty:
            logger.warning("No correlations computed. Check data content.")
            # Create empty result file with headers
            pd.DataFrame(columns=['pupil_metric', 'proxy_variable', 'correlation', 
                                 'p_value_raw', 'p_value_fdr', 'n_samples']).to_csv(output_file, index=False)
        else:
            # Save results
            save_results(results_df, output_file)
            logger.info(f"Correlation analysis complete. {len(results_df)} correlations computed.")
            
    except Exception as e:
        logger.error(f"Error during correlation analysis: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
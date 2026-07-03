"""
Correlation analysis module for US1.

Calculates Pearson correlations between pupil metrics (peak, mean, quantized)
and cognitive load proxies (search time, fixation count, target salience).
Applies Benjamini-Hochberg FDR correction to p-values.
"""
import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.stats import pearsonr
from typing import List, Tuple, Dict, Optional

# Ensure project root is in path for imports if running as script
if __name__ == "__main__":
    # Add parent directory to path to allow imports from code/
    code_root = Path(__file__).resolve().parent.parent
    if str(code_root) not in sys.path:
        sys.path.insert(0, str(code_root))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
RESULTS_DIR = Path("results")
OUTPUT_FILE = RESULTS_DIR / "correlations.csv"

# Pupil metrics to analyze
PUPIL_METRICS = ['pupil_diameter_peak', 'pupil_diameter_mean', 'pupil_diameter_quantized']

# Load proxies (optional, can be missing if UNFULFILLABLE)
LOAD_PROXIES = ['search_time', 'fixation_count', 'target_salience']

def calculate_pearson_correlation(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    """
    Calculate Pearson correlation coefficient and p-value.
    
    Args:
        x: First variable array
        y: Second variable array
        
    Returns:
        Tuple of (correlation_coefficient, p_value)
        Returns (np.nan, np.nan) if insufficient data or constant variance
    """
    # Filter out NaN values
    valid_mask = ~(np.isnan(x) | np.isnan(y))
    x_valid = x[valid_mask]
    y_valid = y[valid_mask]
    
    if len(x_valid) < 3:
        logger.warning(f"Insufficient data points ({len(x_valid)}) for correlation calculation.")
        return np.nan, np.nan
    
    if np.std(x_valid) == 0 or np.std(y_valid) == 0:
        logger.warning("Constant variance detected; correlation undefined.")
        return np.nan, np.nan
    
    try:
        corr, p_val = pearsonr(x_valid, y_valid)
        return corr, p_val
    except Exception as e:
        logger.error(f"Error calculating Pearson correlation: {e}")
        return np.nan, np.nan

def benjamini_hochberg_fdr(p_values: List[float]) -> List[float]:
    """
    Apply Benjamini-Hochberg False Discovery Rate correction to p-values.
    
    Args:
        p_values: List of raw p-values
        
    Returns:
        List of adjusted p-values (q-values)
    """
    n = len(p_values)
    if n == 0:
        return []
    
    # Filter out NaNs but keep track of original indices
    valid_indices = [i for i, p in enumerate(p_values) if not np.isnan(p)]
    raw_p_vals = [p_values[i] for i in valid_indices]
    
    if len(raw_p_vals) == 0:
        return [np.nan] * n
    
    # Sort p-values and keep original indices
    sorted_indices = np.argsort(raw_p_vals)
    sorted_p_vals = np.array([raw_p_vals[i] for i in sorted_indices])
    
    # Calculate BH adjusted p-values
    adjusted = np.zeros(len(sorted_p_vals))
    for i in range(len(sorted_p_vals)):
        # BH formula: p_adj = p * n / rank
        # rank is 1-based index in sorted list
        rank = i + 1
        adjusted[i] = sorted_p_vals[i] * n / rank
    
    # Ensure monotonicity (cumulative min from the end)
    for i in range(len(adjusted) - 2, -1, -1):
        adjusted[i] = min(adjusted[i], adjusted[i + 1])
    
    # Clip to [0, 1]
    adjusted = np.clip(adjusted, 0, 1)
    
    # Map back to original order
    final_adjusted = [np.nan] * n
    for new_idx, orig_idx in enumerate(valid_indices):
        # Find where this original index ended up in sorted_indices
        sorted_pos = sorted_indices.tolist().index(orig_idx)
        # But we need to map back to the valid_indices list
        # Actually, we sorted raw_p_vals which corresponds to valid_indices
        # sorted_indices here is relative to raw_p_vals
        # So the position in the adjusted array is sorted_indices[i]
        pass
    
    # Let's redo the mapping more carefully
    # sorted_indices tells us which element of raw_p_vals is at position i
    # So adjusted[i] corresponds to raw_p_vals[sorted_indices[i]]
    # raw_p_vals[k] corresponds to p_values[valid_indices[k]]
    # So adjusted[i] corresponds to p_values[valid_indices[sorted_indices[i]]]
    
    final_adjusted = [np.nan] * n
    for i in range(len(adjusted)):
        original_pos_in_valid = sorted_indices[i]
        original_pos_in_full = valid_indices[original_pos_in_valid]
        final_adjusted[original_pos_in_full] = adjusted[i]
    
    return final_adjusted

def load_processed_data(input_path: Path) -> pd.DataFrame:
    """
    Load processed data from the preprocessing stage.
    
    Args:
        input_path: Path to the processed CSV file
        
    Returns:
        DataFrame with trial-wise data
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Processed data file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Check for required columns
    required_cols = ['subject_id', 'trial_id', 'pupil_diameter_mean']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {input_path}: {missing}")
    
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    return df

def extract_pupil_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract or compute pupil metrics (peak, mean, quantized).
    
    Args:
        df: DataFrame with raw pupil data
        
    Returns:
        DataFrame with extracted metrics
    """
    result_df = df.copy()
    
    # Mean is usually already computed
    if 'pupil_diameter_mean' not in result_df.columns:
        if 'pupil_diameter' in result_df.columns:
            result_df['pupil_diameter_mean'] = result_df.groupby(['subject_id', 'trial_id'])['pupil_diameter'].transform('mean')
        else:
            logger.warning("pupil_diameter_mean column not found and cannot be computed.")
            result_df['pupil_diameter_mean'] = np.nan
    
    # Peak: max pupil diameter per trial
    if 'pupil_diameter_peak' not in result_df.columns:
        if 'pupil_diameter' in result_df.columns:
            result_df['pupil_diameter_peak'] = result_df.groupby(['subject_id', 'trial_id'])['pupil_diameter'].transform('max')
        else:
            logger.warning("pupil_diameter_peak column not found and cannot be computed.")
            result_df['pupil_diameter_peak'] = np.nan
    
    # Quantized: discretized pupil diameter (e.g., into quartiles or bins)
    if 'pupil_diameter_quantized' not in result_df.columns:
        if 'pupil_diameter' in result_df.columns:
            # Quantize into 4 bins (quartiles) per subject
            def quantize_by_quartile(group):
                if len(group) > 0:
                    return pd.qcut(group, q=4, labels=False, duplicates='drop')
                return np.nan
            result_df['pupil_diameter_quantized'] = result_df.groupby('subject_id')['pupil_diameter'].transform(quantize_by_quartile)
        else:
            logger.warning("pupil_diameter_quantized column not found and cannot be computed.")
            result_df['pupil_diameter_quantized'] = np.nan
    
    return result_df

def compute_correlations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute Pearson correlations between pupil metrics and load proxies.
    
    Args:
        df: DataFrame with pupil metrics and load proxies
        
    Returns:
        DataFrame with correlation results (metric, proxy, r, p_raw, p_adj)
    """
    results = []
    
    # Get available columns
    available_metrics = [m for m in PUPIL_METRICS if m in df.columns]
    available_proxies = [p for p in LOAD_PROXIES if p in df.columns]
    
    if not available_metrics:
        logger.warning("No pupil metrics available for correlation analysis.")
        return pd.DataFrame(columns=['pupil_metric', 'load_proxy', 'pearson_r', 'p_value_raw', 'p_value_adj'])
    
    if not available_proxies:
        logger.warning("No load proxies available for correlation analysis.")
        return pd.DataFrame(columns=['pupil_metric', 'load_proxy', 'pearson_r', 'p_value_raw', 'p_value_adj'])
    
    logger.info(f"Computing correlations for {len(available_metrics)} metrics x {len(available_proxies)} proxies")
    
    raw_p_values = []
    correlation_data = []
    
    for metric in available_metrics:
        for proxy in available_proxies:
            # Skip if proxy is marked as UNFULFILLABLE in the dataset (check status column if exists)
            if 'status' in df.columns:
                unfulfillable_mask = df['status'] == 'UNFULFILLABLE'
                if unfulfillable_mask.all():
                    logger.info(f"Skipping {metric} vs {proxy}: all data marked UNFULFILLABLE")
                    corr, p_val = np.nan, np.nan
                else:
                    # Filter out UNFULFILLABLE rows for this specific proxy if possible
                    # For now, we'll just use all data and let NaN handling in pearsonr do its job
                    corr, p_val = calculate_pearson_correlation(df[metric].values, df[proxy].values)
            else:
                corr, p_val = calculate_pearson_correlation(df[metric].values, df[proxy].values)
            
            raw_p_values.append(p_val)
            correlation_data.append({
                'pupil_metric': metric,
                'load_proxy': proxy,
                'pearson_r': corr,
                'p_value_raw': p_val
            })
    
    # Apply FDR correction
    adj_p_values = benjamini_hochberg_fdr(raw_p_values)
    
    # Add adjusted p-values to results
    for i, data in enumerate(correlation_data):
        data['p_value_adj'] = adj_p_values[i]
    
    return pd.DataFrame(correlation_data)

def save_results(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save correlation results to CSV.
    
    Args:
        df: DataFrame with correlation results
        output_path: Path to save the CSV file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved correlation results to {output_path}")

def main():
    """Main entry point for correlation analysis."""
    # Determine input file path
    # Expected to be generated by preprocessing pipeline
    input_file = Path("data/processed/trialwise_features.csv")
    
    # If input doesn't exist, try to find any processed file
    if not input_file.exists():
        processed_dir = Path("data/processed")
        if processed_dir.exists():
            csv_files = list(processed_dir.glob("*.csv"))
            if csv_files:
                input_file = csv_files[0]
                logger.info(f"Using alternative input file: {input_file}")
            else:
                logger.error("No processed CSV files found in data/processed/")
                sys.exit(1)
        else:
            logger.error("data/processed/ directory does not exist.")
            sys.exit(1)
    
    try:
        # Load data
        df = load_processed_data(input_file)
        
        # Extract pupil metrics
        df = extract_pupil_metrics(df)
        
        # Compute correlations
        results_df = compute_correlations(df)
        
        # Save results
        save_results(results_df, OUTPUT_FILE)
        
        # Print summary
        if not results_df.empty:
            significant = results_df[results_df['p_value_adj'] < 0.05]
            logger.info(f"Total correlations computed: {len(results_df)}")
            logger.info(f"Significant (FDR < 0.05): {len(significant)}")
            if not significant.empty:
                logger.info("Significant correlations:")
                print(significant.to_string(index=False))
        else:
            logger.warning("No correlations could be computed.")
            
    except Exception as e:
        logger.error(f"Error during correlation analysis: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

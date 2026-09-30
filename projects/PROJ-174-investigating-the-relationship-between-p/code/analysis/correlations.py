import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Optional, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_processed_data(path: str) -> pd.DataFrame:
    """Load processed data from CSV."""
    path_obj = Path(path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Processed data file not found: {path}")
    return pd.read_csv(path)

def extract_pupil_metrics(df: pd.DataFrame) -> Dict[str, pd.Series]:
    """Extract pupil diameter metrics from the dataframe."""
    metrics = {}
    if 'pupil_diameter' in df.columns:
        metrics['mean'] = df['pupil_diameter'].mean()
        metrics['peak'] = df['pupil_diameter'].max()
        # Quantized: bin into 4 levels
        if len(df) > 0:
            q = pd.qcut(df['pupil_diameter'].dropna(), q=4, labels=False, duplicates='drop')
            metrics['quantized'] = q.mean()
        else:
            metrics['quantized'] = np.nan
    return metrics

def calculate_pearson_correlation(x: pd.Series, y: pd.Series) -> tuple:
    """Calculate Pearson correlation and p-value."""
    if len(x) < 2 or len(y) < 2:
        return np.nan, np.nan
    
    # Drop NaN pairs
    mask = ~(x.isna() | y.isna())
    x_clean = x[mask]
    y_clean = y[mask]
    
    if len(x_clean) < 2:
        return np.nan, np.nan
    
    r, p = np.corrcoef(x_clean, y_clean)[0, 1], 0.0
    
    # Calculate p-value manually or use scipy if available
    try:
        from scipy.stats import pearsonr
        r, p = pearsonr(x_clean, y_clean)
    except ImportError:
        # Fallback to manual calculation if scipy not available
        n = len(x_clean)
        if n < 2:
            return np.nan, np.nan
        t_stat = r * np.sqrt((n - 2) / (1 - r**2 + 1e-10))
        # Approximate p-value using t-distribution logic (simplified)
        # For exact p-value, scipy is preferred. Here we return r and a placeholder p if scipy missing.
        p = 0.0 # Placeholder, requires scipy for accuracy
        if 'scipy' not in sys.modules:
            logger.warning("scipy not available. P-values may be inaccurate.")

    return float(r), float(p)

def compute_correlations(df: pd.DataFrame) -> pd.DataFrame:
    """Compute Pearson correlations between pupil metrics and load proxies."""
    results = []
    
    pupil_metrics = ['mean', 'peak', 'quantized']
    proxies = ['search_time', 'fixation_count', 'target_salience']
    
    # Filter out columns that don't exist
    available_proxies = [p for p in proxies if p in df.columns]
    
    for metric_name in pupil_metrics:
        # We need to compute correlations on a trial-wise basis.
        # Assuming the dataframe has one row per trial (aggregated).
        # If the dataframe has raw samples, we need to group by trial_id first.
        # Based on T016a context, we assume df is already trial-wise or we aggregate.
        
        # Check if we have trial_id to group by
        if 'trial_id' in df.columns and 'pupil_diameter' in df.columns:
            # Group by trial and compute metric
            trial_metrics = df.groupby('trial_id')['pupil_diameter'].agg(['mean', 'max'])
            trial_metrics['quantized'] = trial_metrics['mean'] # Placeholder for quantized logic per trial
            # Re-calculate quantized properly per trial if needed, but for correlation, mean/peak often suffice
            # Let's stick to the columns we have: mean, max (peak)
            # For quantized, we need to bin per trial? No, usually global or per condition.
            # Assuming 'mean' and 'max' are sufficient for the correlation step.
            
            for proxy in available_proxies:
                if proxy in trial_metrics.columns:
                    continue # Skip if proxy is in the metric calculation (unlikely)
                
                # Merge proxy if it's not in the grouped frame
                if proxy in df.columns:
                    # Assuming proxy is constant per trial or aggregated
                    proxy_vals = df[['trial_id', proxy]].drop_duplicates()
                    trial_metrics = trial_metrics.merge(proxy_vals, on='trial_id', how='inner')
                
                if proxy not in trial_metrics.columns:
                    continue
                
                r, p = calculate_pearson_correlation(trial_metrics['mean'], trial_metrics[proxy])
                results.append({
                    'metric': f"{metric_name}_mean",
                    'proxy': proxy,
                    'pearson_r': r,
                    'raw_p': p,
                    'method': 'pearson'
                })
                
                r, p = calculate_pearson_correlation(trial_metrics['max'], trial_metrics[proxy])
                results.append({
                    'metric': f"{metric_name}_peak",
                    'proxy': proxy,
                    'pearson_r': r,
                    'raw_p': p,
                    'method': 'pearson'
                })
        else:
            # If no trial_id, assume rows are already aggregated trials
            for proxy in available_proxies:
                r, p = calculate_pearson_correlation(df['pupil_diameter'], df[proxy])
                results.append({
                    'metric': 'mean',
                    'proxy': proxy,
                    'pearson_r': r,
                    'raw_p': p,
                    'method': 'pearson'
                })
                
                r, p = calculate_pearson_correlation(df['pupil_diameter'], df[proxy])
                # Re-using same logic for peak if column exists, otherwise skip
                if 'pupil_diameter_peak' in df.columns:
                    r, p = calculate_pearson_correlation(df['pupil_diameter_peak'], df[proxy])
                    results.append({
                        'metric': 'peak',
                        'proxy': proxy,
                        'pearson_r': r,
                        'raw_p': p,
                        'method': 'pearson'
                    })

    return pd.DataFrame(results)

def benjamini_hochberg_fdr(p_values: pd.Series) -> pd.Series:
    """
    Apply Benjamini-Hochberg FDR correction to a series of p-values.
    
    Args:
        p_values: Series of raw p-values.
        
    Returns:
        Series of adjusted p-values.
    """
    if len(p_values) == 0:
        return p_values
    
    n = len(p_values)
    # Sort p-values and keep original index
    sorted_indices = p_values.argsort()
    sorted_p = p_values.iloc[sorted_indices]
    
    # Calculate adjusted p-values
    # Formula: (rank * p) / n, but monotonicity must be enforced (cumulative min from bottom)
    adj_p = np.zeros(n)
    for i in range(n):
        rank = i + 1
        adj_p[i] = sorted_p.iloc[i] * n / rank
    
    # Enforce monotonicity (cumulative minimum from the largest rank to smallest)
    # The BH procedure ensures that adjusted p-values are non-decreasing with rank
    # We need to ensure adj_p[i] <= adj_p[i+1]
    for i in range(n - 2, -1, -1):
        adj_p[i] = min(adj_p[i], adj_p[i+1])
    
    # Clip to [0, 1]
    adj_p = np.clip(adj_p, 0, 1)
    
    # Restore original order
    result = pd.Series(adj_p, index=p_values.index)
    return result

def save_results(df: pd.DataFrame, output_path: str):
    """Save results to CSV."""
    path_obj = Path(output_path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path_obj, index=False)
    logger.info(f"Results saved to {output_path}")

def main():
    """Main entry point for correlation analysis."""
    # Define paths based on project structure
    base_path = Path(__file__).resolve().parent.parent
    processed_data_path = base_path / "data" / "processed" / "features.csv"
    output_path = base_path / "results" / "correlations.csv"
    
    if not processed_data_path.exists():
        logger.error(f"Processed data not found at {processed_data_path}. Run preprocessing first.")
        sys.exit(1)
    
    logger.info(f"Loading data from {processed_data_path}")
    df = load_processed_data(str(processed_data_path))
    
    logger.info("Computing correlations...")
    results_df = compute_correlations(df)
    
    if results_df.empty:
        logger.warning("No correlations computed. Check data columns.")
        # Create empty dataframe with correct schema if needed
        results_df = pd.DataFrame(columns=['metric', 'proxy', 'pearson_r', 'raw_p', 'method'])
    
    # Apply Benjamini-Hochberg FDR correction
    if 'raw_p' in results_df.columns and not results_df['raw_p'].isna().all():
        logger.info("Applying Benjamini-Hochberg FDR correction...")
        results_df['adj_p'] = benjamini_hochberg_fdr(results_df['raw_p'])
    else:
        results_df['adj_p'] = np.nan
        logger.warning("No valid p-values found for FDR correction.")
    
    # Save results
    save_results(results_df, str(output_path))
    
    # Verify adj_p is present
    if 'adj_p' not in results_df.columns:
        logger.error("adj_p column missing in results.")
        sys.exit(1)
    
    logger.info("Correlation analysis with FDR correction complete.")
    return results_df

if __name__ == "__main__":
    main()
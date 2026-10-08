import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED_PATH = PROJECT_ROOT / "data" / "processed" / "features.csv"
RESULTS_DIR = PROJECT_ROOT / "results"
CORRELATIONS_OUTPUT_PATH = RESULTS_DIR / "correlations.csv"

def load_processed_data(path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the preprocessed features dataset.
    """
    if path is None:
        path = DATA_PROCESSED_PATH
    
    if not path.exists():
        raise FileNotFoundError(f"Processed data file not found at {path}. "
                                "Ensure T013-T016a have run successfully.")
    
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} rows from {path}")
    return df

def extract_pupil_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure pupil metrics are present.
    This function assumes T016a has run and appended:
    pupil_peak, pupil_mean, pupil_q25, pupil_q50, pupil_q75
    """
    required_metrics = ['pupil_peak', 'pupil_mean', 'pupil_q25', 'pupil_q50', 'pupil_q75']
    missing = [m for m in required_metrics if m not in df.columns]
    
    if missing:
        raise ValueError(f"Missing required pupil metrics columns: {missing}. "
                         "Ensure T016a (metrics.py) has been executed.")
    
    logger.info("Pupil metrics columns verified.")
    return df

def calculate_pearson_correlation(x: pd.Series, y: pd.Series) -> Tuple[float, float]:
    """
    Calculate Pearson correlation and p-value.
    Handles NaNs by dropping pairwise.
    """
    # Drop NaNs pairwise
    valid_mask = x.notna() & y.notna()
    if valid_mask.sum() < 2:
        return np.nan, np.nan
    
    x_valid = x[valid_mask]
    y_valid = y[valid_mask]
    
    r, p = np.corrcoef(x_valid, y_valid)
    # np.corrcoef returns a 2x2 matrix. [0,1] is the correlation.
    # However, if inputs are 1D, it returns a 2x2.
    # Let's use scipy.stats for a cleaner p-value calculation if available, 
    # but numpy is sufficient for basic correlation.
    # To get p-value correctly with numpy:
    # r = corrcoef[0,1]
    # t = r * sqrt((n-2)/(1-r^2))
    # p = 2 * (1 - t_cdf(|t|, n-2))
    
    # Using scipy is safer for p-values if available, but let's stick to numpy/scipy standard
    # Since 'scipy' is in requirements, we should use it for p-values.
    from scipy import stats
    
    r, p = stats.pearsonr(x_valid, y_valid)
    return r, p

def compute_correlations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute Pearson correlations between pupil metrics and cognitive load proxies.
    
    Metrics: pupil_peak, pupil_mean, pupil_q25, pupil_q50, pupil_q75
    Proxies: search_time, target_salience, fixation_count
    
    Returns a DataFrame with columns:
    metric, proxy, pearson_r, raw_p, method
    """
    metrics = ['pupil_peak', 'pupil_mean', 'pupil_q25', 'pupil_q50', 'pupil_q75']
    proxies = ['search_time', 'target_salience', 'fixation_count']
    
    results = []
    
    for metric in metrics:
        for proxy in proxies:
            if metric not in df.columns or proxy not in df.columns:
                logger.warning(f"Skipping correlation: {metric} vs {proxy} (column missing)")
                continue
            
            r, p = calculate_pearson_correlation(df[metric], df[proxy])
            
            results.append({
                'metric': metric,
                'proxy': proxy,
                'pearson_r': r,
                'raw_p': p,
                'method': 'pearson'
            })
    
    return pd.DataFrame(results)

def save_results(df: pd.DataFrame, output_path: Optional[Path] = None) -> None:
    """
    Save the correlation results to CSV.
    """
    if output_path is None:
        output_path = CORRELATIONS_OUTPUT_PATH
    
    # Ensure results directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} correlation results to {output_path}")

def apply_fdr_correction(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply Benjamini-Hochberg FDR correction to raw p-values.
    Note: This is Part 2 (T016c), but included here for completeness if needed.
    T016b specifically produces the RAW correlations.
    """
    from statsmodels.stats.multitest import multipletests
    
    # Filter out NaN p-values for correction
    valid_p = df['raw_p'].dropna()
    if len(valid_p) == 0:
        logger.warning("No valid p-values to correct.")
        return df
    
    _, adj_p, _, _ = multipletests(valid_p, method='fdr_bh')
    
    # Map back to original dataframe
    # Create a mapping of index to adjusted p-value
    # We need to be careful with indices if we dropped NaNs
    valid_indices = df[df['raw_p'].notna()].index
    adj_p_map = dict(zip(valid_indices, adj_p))
    
    df['adj_p'] = df.index.map(adj_p_map).fillna(np.nan)
    return df

def run_correlation_pipeline() -> pd.DataFrame:
    """
    Main pipeline function for T016b.
    1. Load processed data.
    2. Verify pupil metrics.
    3. Compute correlations.
    4. Save raw results.
    """
    logger.info("Starting correlation analysis pipeline (T016b).")
    
    # 1. Load Data
    df = load_processed_data()
    
    # 2. Verify Metrics
    df = extract_pupil_metrics(df)
    
    # 3. Compute Correlations
    results_df = compute_correlations(df)
    
    # 4. Save Results (Raw)
    save_results(results_df)
    
    logger.info("Correlation analysis pipeline (T016b) completed.")
    return results_df

def main():
    """
    Entry point for script execution.
    """
    try:
        results = run_correlation_pipeline()
        print(f"Successfully generated correlations. Output: {CORRELATIONS_OUTPUT_PATH}")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
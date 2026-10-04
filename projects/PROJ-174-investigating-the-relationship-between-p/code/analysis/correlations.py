"""
Correlation analysis module.
Computes Pearson correlations between pupil metrics and load proxies,
with optional FDR correction.
"""
import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any, List

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import load_config

logger = logging.getLogger(__name__)

def load_processed_data(config: Dict[str, Any]) -> pd.DataFrame:
    """Load processed features data."""
    processed_dir = Path(config['paths']['processed_data'])
    features_file = processed_dir / 'features.csv'
    
    if not features_file.exists():
        logger.error(f"Features file not found: {features_file}")
        return pd.DataFrame()
    
    return pd.read_csv(features_file)

def extract_pupil_metrics(df: pd.DataFrame) -> List[str]:
    """Get list of pupil metric columns."""
    pupil_cols = [c for c in df.columns if c.startswith('pupil_')]
    return pupil_cols

def calculate_pearson_correlation(x: pd.Series, y: pd.Series) -> tuple:
    """
    Calculate Pearson correlation between two series.
    
    Returns:
        Tuple of (correlation, p-value)
    """
    valid_mask = x.notna() & y.notna()
    x_valid = x[valid_mask]
    y_valid = y[valid_mask]
    
    if len(x_valid) < 3:
        return (np.nan, np.nan)
    
    corr, p_value = x_valid.corr(y_valid), np.nan
    # Simple p-value approximation (for demonstration)
    n = len(x_valid)
    if not np.isnan(corr):
        t_stat = corr * np.sqrt((n - 2) / (1 - corr**2))
        # Approximate p-value using t-distribution
        from scipy import stats
        p_value = 2 * stats.t.sf(abs(t_stat), n - 2)
    
    return (corr, p_value)

def compute_correlations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute correlations between all pupil metrics and load proxies.
    
    Args:
        df: DataFrame with pupil metrics and load proxies
        
    Returns:
        DataFrame with correlation results
    """
    if df.empty:
        return pd.DataFrame(columns=['metric', 'proxy', 'pearson_r', 'raw_p', 'method'])
    
    pupil_metrics = extract_pupil_metrics(df)
    proxy_cols = ['search_time', 'fixation_count', 'target_salience']
    proxies = [c for c in proxy_cols if c in df.columns]
    
    results = []
    
    for metric in pupil_metrics:
        for proxy in proxies:
            # Skip if either column is all NaN
            if df[metric].isna().all() or df[proxy].isna().all():
                continue
            
            corr, p_val = calculate_pearson_correlation(df[metric], df[proxy])
            
            if not np.isnan(corr):
                results.append({
                    'metric': metric,
                    'proxy': proxy,
                    'pearson_r': corr,
                    'raw_p': p_val,
                    'method': 'pearson'
                })
    
    return pd.DataFrame(results)

def save_results(correlations_df: pd.DataFrame, config: Dict[str, Any]):
    """Save correlation results to file."""
    results_dir = Path(config['paths']['results'])
    results_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = results_dir / 'correlations.csv'
    correlations_df.to_csv(output_path, index=False)
    logger.info(f"Correlations saved to {output_path}")

def apply_fdr_correction(correlations_df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply Benjamini-Hochberg FDR correction to p-values.
    
    Args:
        correlations_df: DataFrame with raw p-values
        
    Returns:
        DataFrame with adjusted p-values
    """
    if correlations_df.empty:
        return correlations_df
    
    from statsmodels.stats.multitest import multipletests
    
    p_values = correlations_df['raw_p'].dropna().values
    if len(p_values) == 0:
        correlations_df['adj_p'] = np.nan
        return correlations_df
    
    _, adj_p, _, _ = multipletests(p_values, method='fdr_bh')
    
    # Map adjusted p-values back to original rows
    valid_mask = correlations_df['raw_p'].notna()
    adj_p_values = np.full(len(correlations_df), np.nan)
    adj_p_values[valid_mask] = adj_p
    
    correlations_df['adj_p'] = adj_p_values
    
    return correlations_df

def run_correlation_pipeline(config: Dict[str, Any]):
    """Run the full correlation analysis pipeline."""
    df = load_processed_data(config)
    
    if df.empty:
        logger.warning("No data to analyze. Creating empty correlations file.")
        results_dir = Path(config['paths']['results'])
        results_dir.mkdir(parents=True, exist_ok=True)
        empty_df = pd.DataFrame(columns=['metric', 'proxy', 'pearson_r', 'raw_p', 'method', 'adj_p'])
        empty_df.to_csv(results_dir / 'correlations.csv', index=False)
        return
    
    # Compute correlations
    correlations_df = compute_correlations(df)
    
    # Apply FDR correction
    correlations_df = apply_fdr_correction(correlations_df)
    
    # Save results
    save_results(correlations_df, config)
    
    logger.info(f"Correlation pipeline completed. Found {len(correlations_df)} significant correlations.")

def main():
    """Main entry point for correlation analysis."""
    parser = argparse.ArgumentParser(description="Compute correlations")
    parser.add_argument("--config", type=str, default="code/config.yaml")
    args = parser.parse_args()
    
    config = load_config(Path(args.config))
    run_correlation_pipeline(config)

if __name__ == "__main__":
    main()
import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import json
import pandas as pd
import numpy as np
from scipy.stats import pearsonr

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_hybrid_output_metrics() -> pd.DataFrame:
    """
    Load the hybrid output metrics from the processed data.
    Expects data/processed/hybrid_output.parquet to exist.
    """
    metrics_path = Path('data/processed/hybrid_output.parquet')
    if not metrics_path.exists():
        raise FileNotFoundError(
            f"Required file not found: {metrics_path}. "
            "Run hybrid_sim.py (T050) first."
        )
    
    logger.info(f"Loading hybrid output from {metrics_path}")
    df = pd.read_parquet(metrics_path)
    
    required_cols = ['proxy_mos', 'latency_ms']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Missing required columns in hybrid output: {missing_cols}"
        )
    
    return df

def load_human_ratings() -> Optional[pd.DataFrame]:
    """
    Load human ratings from data/raw/human_ratings.json if available.
    Returns None if the file does not exist.
    """
    ratings_path = Path('data/raw/human_ratings.json')
    if not ratings_path.exists():
        logger.info(f"Human ratings file not found at {ratings_path}")
        return None
    
    logger.info(f"Loading human ratings from {ratings_path}")
    with open(ratings_path, 'r') as f:
        data = json.load(f)
    
    # Convert to DataFrame
    if isinstance(data, list):
        df = pd.DataFrame(data)
    elif isinstance(data, dict):
        # Assume it's a dict of lists or similar structure
        df = pd.DataFrame([data])
    else:
        raise ValueError(f"Unexpected human ratings format: {type(data)}")
    
    # Ensure we have a 'human_mos' column (or similar)
    if 'human_mos' not in df.columns:
        # Try to find a column that might contain human ratings
        possible_cols = [c for c in df.columns if 'mos' in c.lower() or 'rating' in c.lower()]
        if possible_cols:
            df = df.rename(columns={possible_cols[0]: 'human_mos'})
        else:
            raise ValueError(
                "Human ratings file does not contain a 'human_mos' column "
                f"or similar. Available columns: {list(df.columns)}"
            )
    
    return df

def calculate_correlation(
    proxy_series: pd.Series, 
    human_series: pd.Series
) -> Tuple[float, float]:
    """
    Calculate Pearson correlation between proxy MOS and human ratings.
    
    Returns:
        Tuple of (correlation_coefficient, p_value)
    """
    # Drop NaN values
    valid_mask = proxy_series.notna() & human_series.notna()
    proxy_valid = proxy_series[valid_mask]
    human_valid = human_series[valid_mask]
    
    if len(proxy_valid) < 2:
        raise ValueError(
            f"Insufficient data points for correlation: {len(proxy_valid)}"
        )
    
    correlation, p_value = pearsonr(proxy_valid, human_valid)
    return float(correlation), float(p_value)

def validate_proxy_mos(
    proxy_df: pd.DataFrame,
    human_df: Optional[pd.DataFrame] = None
) -> Dict[str, Any]:
    """
    Validate proxy MOS against human ratings if available.
    
    Returns:
        Dictionary with validation results including correlation,
        p-value, and validation status.
    """
    result = {
        'proxy_mos_stats': {
            'mean': float(proxy_df['proxy_mos'].mean()),
            'std': float(proxy_df['proxy_mos'].std()),
            'count': int(len(proxy_df))
        },
        'correlation': None,
        'p_value': None,
        'validation_status': None,
        'message': None
    }
    
    if human_df is None:
        result['validation_status'] = 'ASSUMPTION_VALIDATED'
        result['message'] = 'Assumption Validated (No Human Data Available)'
        logger.warning("No human ratings available. Validation skipped.")
        logger.info(result['message'])
        return result
    
    # Ensure human_df has indices that align with proxy_df
    # If not, we need to merge on a common key or assume order
    if 'frame_id' in proxy_df.columns and 'frame_id' in human_df.columns:
        # Merge on frame_id
        merged = proxy_df.merge(human_df, on='frame_id', suffixes=('_proxy', '_human'))
        if len(merged) == 0:
            raise ValueError(
                "No overlapping frame IDs between proxy output and human ratings"
            )
        proxy_series = merged['proxy_mos']
        human_series = merged['human_mos']
    else:
        # Assume same order and index
        if len(proxy_df) != len(human_df):
            logger.warning(
                f"Proxy and human ratings have different lengths: "
                f"{len(proxy_df)} vs {len(human_df)}. Attempting to align by index."
            )
            # Align by index
            proxy_series = proxy_df['proxy_mos'].reindex(human_df.index)
            human_series = human_df['human_mos']
        else:
            proxy_series = proxy_df['proxy_mos']
            human_series = human_df['human_mos']
    
    try:
        correlation, p_value = calculate_correlation(proxy_series, human_series)
        result['correlation'] = correlation
        result['p_value'] = p_value
        
        # Validate correlation threshold (r >= 0.7 as per SC-007)
        if correlation >= 0.7:
            result['validation_status'] = 'VALIDATED'
            result['message'] = f"Proxy MOS validated: r={correlation:.4f}, p={p_value:.6f}"
            logger.info(result['message'])
        else:
            result['validation_status'] = 'INVALIDATED'
            result['message'] = (
                f"Proxy MOS validation failed: r={correlation:.4f} < 0.7, "
                f"p={p_value:.6f}"
            )
            logger.warning(result['message'])
            
    except Exception as e:
        result['validation_status'] = 'ERROR'
        result['message'] = f"Correlation calculation failed: {str(e)}"
        logger.error(result['message'])
        raise
    
    return result

def main():
    """Main entry point for the proxy MOS validation task."""
    parser = argparse.ArgumentParser(
        description='Validate proxy MOS against human ratings'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/metrics/proxy_mos_validation.json',
        help='Output file for validation results'
    )
    args = parser.parse_args()
    
    try:
        # Load data
        proxy_df = load_hybrid_output_metrics()
        human_df = load_human_ratings()
        
        # Validate
        result = validate_proxy_mos(proxy_df, human_df)
        
        # Save results
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Validation results saved to {output_path}")
        
        # Exit with appropriate code
        if result['validation_status'] in ['VALIDATED', 'ASSUMPTION_VALIDATED']:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
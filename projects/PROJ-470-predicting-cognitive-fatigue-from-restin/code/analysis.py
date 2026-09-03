import os
import sys
import json
import logging
import yaml
import pandas as pd
import numpy as np
from scipy import stats
from pathlib import Path
from typing import Tuple, List, Dict, Any

# Configuration paths
CONFIG_PATH = "code/config.yaml"
COMPLEXITY_METRICS_PATH = "data/analysis/complexity_metrics.csv"
DELTA_SCORES_PATH = "data/analysis/delta_scores.csv"
CORRELATION_RESULTS_PATH = "data/analysis/correlation_results.csv"
LOG_PATH = "data/analysis/analysis.log"

def load_config() -> Dict[str, Any]:
    """Load configuration from YAML file."""
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)

def setup_logger(name: str, log_file: str = None) -> logging.Logger:
    """Setup logging infrastructure."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # File handler
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)
        fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(fh)
    
    # Stream handler
    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    sh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(sh)
    
    return logger

def validate_metadata(df: pd.DataFrame) -> bool:
    """
    Validate that the dataframe contains required columns for correlation analysis.
    Required columns: 'participant_id', 'pre_fatigue', 'post_fatigue', 'channel', 'lzc', 'pe'
    """
    required_cols = ['participant_id', 'pre_fatigue', 'post_fatigue', 'channel', 'lzc', 'pe']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Check for paired data (pre and post fatigue ratings)
    if df['pre_fatigue'].isna().all() or df['post_fatigue'].isna().all():
        raise ValueError("No valid pre/post fatigue ratings found in the dataset.")
    
    return True

def calculate_delta_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate delta scores (Post - Pre) for both complexity and fatigue.
    """
    df = df.copy()
    
    # Calculate fatigue delta
    df['fatigue_delta'] = df['post_fatigue'] - df['pre_fatigue']
    
    # Calculate complexity deltas if we have baseline vs post-fatigue complexity
    # Assuming the data is structured such that we have pre/post complexity per channel
    # If the data is already aggregated by condition, we calculate deltas per participant/channel
    
    # For this implementation, we assume the input has pre/post complexity metrics
    # If not present, we calculate based on available data
    if 'pre_lzc' in df.columns and 'post_lzc' in df.columns:
        df['lzc_delta'] = df['post_lzc'] - df['pre_lzc']
    if 'pre_pe' in df.columns and 'post_pe' in df.columns:
        df['pe_delta'] = df['post_pe'] - df['pre_pe']
    
    return df

def run_correlation_analysis(
    df: pd.DataFrame,
    complexity_col: str,
    fatigue_col: str,
    method: str = 'spearman'
) -> Tuple[float, float]:
    """
    Compute Pearson or Spearman correlation between complexity and fatigue metrics.
    
    Args:
        df: DataFrame containing the metrics
        complexity_col: Name of the complexity column to correlate
        fatigue_col: Name of the fatigue column to correlate
        method: 'pearson' or 'spearman'
    
    Returns:
        Tuple of (correlation_coefficient, p_value)
    """
    # Drop rows with NaN in either column
    valid_data = df[[complexity_col, fatigue_col]].dropna()
    
    if len(valid_data) < 2:
        return np.nan, np.nan
    
    if method == 'pearson':
        corr, p_val = stats.pearsonr(valid_data[complexity_col], valid_data[fatigue_col])
    elif method == 'spearman':
        corr, p_val = stats.spearmanr(valid_data[complexity_col], valid_data[fatigue_col])
    else:
        raise ValueError(f"Unsupported correlation method: {method}")
    
    return corr, p_val

def write_validation_report(log: logging.Logger, df: pd.DataFrame) -> None:
    """Write a validation report to the log."""
    log.info(f"Validation successful. Loaded {len(df)} records.")
    log.info(f"Columns: {list(df.columns)}")
    log.info(f"Unique participants: {df['participant_id'].nunique()}")
    log.info(f"Unique channels: {df['channel'].nunique()}")

def main():
    """Main entry point for the analysis pipeline."""
    logger = setup_logger('analysis', LOG_PATH)
    logger.info("Starting analysis pipeline.")
    
    try:
        # Load configuration
        config = load_config()
        logger.info(f"Loaded config: {config}")
        
        # Load complexity metrics
        if not os.path.exists(COMPLEXITY_METRICS_PATH):
            logger.error(f"Complexity metrics file not found: {COMPLEXITY_METRICS_PATH}")
            logger.error("Run code/features.py first to generate complexity metrics.")
            sys.exit(1)
        
        df = pd.read_csv(COMPLEXITY_METRICS_PATH)
        logger.info(f"Loaded {len(df)} records from {COMPLEXITY_METRICS_PATH}")
        
        # Validate metadata
        validate_metadata(df)
        logger.info("Metadata validation passed.")
        
        # Calculate delta scores (T019)
        df = calculate_delta_scores(df)
        logger.info("Delta scores calculated.")
        
        # Save delta scores if needed
        if os.path.exists(DELTA_SCORES_PATH):
            df.to_csv(DELTA_SCORES_PATH, index=False)
            logger.info(f"Delta scores saved to {DELTA_SCORES_PATH}")
        
        # Perform correlation analysis (T020)
        logger.info("Running correlation analysis...")
        
        results = []
        channels = df['channel'].unique()
        
        for channel in channels:
            channel_df = df[df['channel'] == channel]
            
            # Correlate LZC with fatigue delta
            lzc_corr, lzc_p = run_correlation_analysis(
                channel_df, 'lzc', 'fatigue_delta', method='spearman'
            )
            
            # Correlate PE with fatigue delta
            pe_corr, pe_p = run_correlation_analysis(
                channel_df, 'pe', 'fatigue_delta', method='spearman'
            )
            
            # Also check Pearson
            lzc_pearson, lzc_pearson_p = run_correlation_analysis(
                channel_df, 'lzc', 'fatigue_delta', method='pearson'
            )
            
            pe_pearson, pe_pearson_p = run_correlation_analysis(
                channel_df, 'pe', 'fatigue_delta', method='pearson'
            )
            
            results.append({
                'channel': channel,
                'metric': 'lzc',
                'method': 'spearman',
                'correlation': lzc_corr,
                'p_value': lzc_p
            })
            results.append({
                'channel': channel,
                'metric': 'pe',
                'method': 'spearman',
                'correlation': pe_corr,
                'p_value': pe_p
            })
            results.append({
                'channel': channel,
                'metric': 'lzc',
                'method': 'pearson',
                'correlation': lzc_pearson,
                'p_value': lzc_pearson_p
            })
            results.append({
                'channel': channel,
                'metric': 'pe',
                'method': 'pearson',
                'correlation': pe_pearson,
                'p_value': pe_pearson_p
            })
        
        # Create results DataFrame
        results_df = pd.DataFrame(results)
        
        # Save results
        os.makedirs(os.path.dirname(CORRELATION_RESULTS_PATH), exist_ok=True)
        results_df.to_csv(CORRELATION_RESULTS_PATH, index=False)
        
        logger.info(f"Correlation results saved to {CORRELATION_RESULTS_PATH}")
        logger.info(f"Results: {len(results_df)} correlations computed.")
        
        # Print summary
        logger.info("Correlation Analysis Summary:")
        logger.info(results_df.to_string())
        
    except Exception as e:
        logger.error(f"Analysis pipeline failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
    
    logger.info("Analysis pipeline complete.")

if __name__ == "__main__":
    main()
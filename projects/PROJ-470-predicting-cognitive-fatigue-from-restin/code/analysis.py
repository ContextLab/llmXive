"""
Analysis module for correlating EEG complexity metrics with fatigue scores.
Implements Pearson/Spearman correlation as per FR-004.
"""
import os
import sys
import json
import yaml
import pandas as pd
import numpy as np
from scipy import stats
from pathlib import Path
import logging

# Import logging utilities
from utils.logging import get_logger

def load_config(config_path="code/config.yaml"):
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def setup_logger(name, log_file='logs/analysis.log', level=logging.INFO):
    """Setup logging infrastructure."""
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(level)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)
    
    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger

def write_validation_report(report_path, status, message):
    """Write validation report to JSON file."""
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    report = {
        "status": status,
        "message": message,
        "timestamp": pd.Timestamp.now().isoformat()
    }
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

def validate_metadata(metadata_path):
    """
    Validate that metadata contains required paired fatigue ratings.
    Exits with code 1 if paired data is missing (per T019 requirements).
    """
    logger = setup_logger("analysis")
    
    if not os.path.exists(metadata_path):
        logger.error(f"Metadata file not found: {metadata_path}")
        write_validation_report(
            "data/analysis/validation_report.json",
            "ERROR",
            f"Metadata file not found: {metadata_path}"
        )
        sys.exit(1)
    
    try:
        metadata = pd.read_csv(metadata_path)
    except Exception as e:
        logger.error(f"Failed to read metadata: {e}")
        write_validation_report(
            "data/analysis/validation_report.json",
            "ERROR",
            f"Failed to read metadata: {e}"
        )
        sys.exit(1)
    
    # Check for paired fatigue columns
    paired_columns = ['pre_fatigue', 'post_fatigue', 'fatigue_pre', 'fatigue_post']
    available_pairs = [col for col in paired_columns if col in metadata.columns]
    
    if len(available_pairs) < 2:
        logger.error("ERROR: Paired pre/post fatigue data required by FR-004 not found.")
        logger.error(f"Available columns: {list(metadata.columns)}")
        write_validation_report(
            "data/analysis/validation_report.json",
            "ERROR",
            "ERROR: Paired pre/post fatigue data required by FR-004 not found. No cross-sectional fallback authorized."
        )
        sys.exit(1)
    
    # Determine which pair to use (prefer standard naming)
    if 'pre_fatigue' in available_pairs and 'post_fatigue' in available_pairs:
        pre_col, post_col = 'pre_fatigue', 'post_fatigue'
    elif 'fatigue_pre' in available_pairs and 'fatigue_post' in available_pairs:
        pre_col, post_col = 'fatigue_pre', 'fatigue_post'
    else:
        # Fallback to any available pair
        pre_col = available_pairs[0]
        post_col = available_pairs[1]
    
    logger.info(f"Using paired columns: {pre_col}, {post_col}")
    return pre_col, post_col

def run_correlation_analysis(lzc_path, pe_path, metadata_path, pre_col, post_col):
    """
    Run Pearson/Spearman correlation analysis between complexity metrics and fatigue delta.
    
    Args:
        lzc_path: Path to LZC metrics CSV
        pe_path: Path to Permutation Entropy metrics CSV
        metadata_path: Path to metadata CSV
        pre_col: Name of pre-fatigue column
        post_col: Name of post-fatigue column
    
    Returns:
        Dictionary containing correlation results
    """
    logger = setup_logger("analysis")
    
    # Load data
    logger.info(f"Loading LZC metrics from {lzc_path}")
    lzc_df = pd.read_csv(lzc_path)
    
    logger.info(f"Loading PE metrics from {pe_path}")
    pe_df = pd.read_csv(pe_path)
    
    logger.info(f"Loading metadata from {metadata_path}")
    metadata = pd.read_csv(metadata_path)
    
    # Calculate fatigue delta
    metadata['fatigue_delta'] = metadata[post_col] - metadata[pre_col]
    
    # Merge with LZC metrics (aggregating by participant if multiple channels)
    # We'll use the mean across channels for the correlation
    lzc_agg = lzc_df.groupby('participant_id')['lzc_value'].mean().reset_index()
    lzc_agg.rename(columns={'lzc_value': 'lzc_mean'}, inplace=True)
    
    # Merge with PE metrics
    pe_agg = pe_df.groupby('participant_id')['pe_value'].mean().reset_index()
    pe_agg.rename(columns={'pe_value': 'pe_mean'}, inplace=True)
    
    # Merge all data
    merged = metadata.merge(lzc_agg, on='participant_id', how='inner')
    merged = merged.merge(pe_agg, on='participant_id', how='inner')
    
    # Exclude participants with missing fatigue ratings
    initial_count = len(merged)
    merged = merged.dropna(subset=['fatigue_delta', 'lzc_mean', 'pe_mean'])
    excluded_count = initial_count - len(merged)
    
    if excluded_count > 0:
        logger.warning(f"Excluded {excluded_count} participants with missing fatigue ratings")
    
    if len(merged) < 2:
        logger.error("Insufficient data after excluding missing values")
        write_validation_report(
            "data/analysis/validation_report.json",
            "ERROR",
            f"Insufficient data after excluding missing values: {len(merged)} participants"
        )
        sys.exit(1)
    
    logger.info(f"Running correlation analysis on {len(merged)} participants")
    
    # Calculate correlations
    results = {
        'lzc': {},
        'pe': {},
        'n_participants': len(merged),
        'method': 'paired'
    }
    
    # LZC correlation
    lzc_pearson_r, lzc_pearson_p = stats.pearsonr(merged['fatigue_delta'], merged['lzc_mean'])
    lzc_spearman_r, lzc_spearman_p = stats.spearmanr(merged['fatigue_delta'], merged['lzc_mean'])
    
    results['lzc']['pearson'] = {
        'r': float(lzc_pearson_r),
        'p': float(lzc_pearson_p)
    }
    results['lzc']['spearman'] = {
        'r': float(lzc_spearman_r),
        'p': float(lzc_spearman_p)
    }
    
    # PE correlation
    pe_pearson_r, pe_pearson_p = stats.pearsonr(merged['fatigue_delta'], merged['pe_mean'])
    pe_spearman_r, pe_spearman_p = stats.spearmanr(merged['fatigue_delta'], merged['pe_mean'])
    
    results['pe']['pearson'] = {
        'r': float(pe_pearson_r),
        'p': float(pe_pearson_p)
    }
    results['pe']['spearman'] = {
        'r': float(pe_spearman_r),
        'p': float(pe_spearman_p)
    }
    
    logger.info(f"LZC Pearson: r={lzc_pearson_r:.4f}, p={lzc_pearson_p:.4f}")
    logger.info(f"LZC Spearman: r={lzc_spearman_r:.4f}, p={lzc_spearman_p:.4f}")
    logger.info(f"PE Pearson: r={pe_pearson_r:.4f}, p={pe_pearson_p:.4f}")
    logger.info(f"PE Spearman: r={pe_spearman_r:.4f}, p={pe_spearman_p:.4f}")
    
    return results

def run_benjamini_hochberg(p_values):
    """
    Apply Benjamini-Hochberg correction for multiple comparisons.
    
    Args:
        p_values: List of p-values to correct
    
    Returns:
        List of adjusted p-values
    """
    p_values = np.array(p_values)
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]
    
    # BH correction
    ranks = np.arange(1, n + 1)
    adjusted = sorted_p * n / ranks
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]  # Ensure monotonicity
    adjusted = np.clip(adjusted, 0, 1)
    
    # Restore original order
    final_adjusted = np.empty(n)
    final_adjusted[sorted_indices] = adjusted
    
    return final_adjusted.tolist()

def calculate_vif(features_df):
    """
    Calculate Variance Inflation Factor for multicollinearity detection.
    
    Args:
        features_df: DataFrame with features (excluding target)
    
    Returns:
        Dictionary of VIF values for each feature
    """
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    
    # Add constant for intercept
    X = features_df.copy()
    X['intercept'] = 1.0
    
    vif_data = {}
    for col in X.columns:
        if col == 'intercept':
            continue
        try:
            vif = variance_inflation_factor(X.values, list(X.columns).index(col))
            vif_data[col] = float(vif)
        except Exception:
            vif_data[col] = float('inf')
    
    return vif_data

def main():
    """Main entry point for analysis pipeline."""
    logger = setup_logger("analysis")
    logger.info("Starting analysis pipeline.")
    
    # Load config
    try:
        config = load_config()
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        sys.exit(1)
    
    # Define paths
    metadata_path = config.get('metadata_path', 'data/raw/metadata.csv')
    lzc_path = config.get('lzc_path', 'data/processed/lzc_metrics.csv')
    pe_path = config.get('pe_path', 'data/processed/pe_metrics.csv')
    
    # Validate metadata
    pre_col, post_col = validate_metadata(metadata_path)
    
    # Run correlation analysis
    results = run_correlation_analysis(lzc_path, pe_path, metadata_path, pre_col, post_col)
    
    # Apply BH correction
    all_p_values = [
        results['lzc']['pearson']['p'],
        results['lzc']['spearman']['p'],
        results['pe']['pearson']['p'],
        results['pe']['spearman']['p']
    ]
    adjusted_p = run_benjamini_hochberg(all_p_values)
    
    results['adjusted_p'] = {
        'lzc_pearson': adjusted_p[0],
        'lzc_spearman': adjusted_p[1],
        'pe_pearson': adjusted_p[2],
        'pe_spearman': adjusted_p[3]
    }
    
    # Save results
    results_path = "data/analysis/correlation_results.json"
    Path(results_path).parent.mkdir(parents=True, exist_ok=True)
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {results_path}")
    logger.info("Analysis pipeline completed successfully.")
    
    return results

if __name__ == "__main__":
    main()

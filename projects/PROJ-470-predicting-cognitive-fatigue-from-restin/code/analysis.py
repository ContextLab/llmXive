import os
import sys
import json
import yaml
import pandas as pd
import numpy as np
from pathlib import Path
import logging
import argparse

# Configure logging
def setup_logger(name, log_file, level=logging.INFO):
    """Set up a logger that writes to both console and file."""
    # Ensure the log directory exists
    log_dir = Path(log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logger('analysis', 'logs/analysis.log')

def load_config(config_path):
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def validate_metadata(metadata_df):
    """
    Validate that metadata contains required fatigue rating columns.
    
    Returns:
        tuple: (mode, message) where mode is 'paired', 'baseline', or 'none'
    """
    columns = metadata_df.columns.tolist()
    
    # Check for paired data (pre and post fatigue ratings)
    paired_vars = ['pre_fatigue', 'fatigue_pre', 'baseline_fatigue', 
                   'post_fatigue', 'fatigue_post', 'end_fatigue']
    
    has_pre = any(var in columns for var in ['pre_fatigue', 'fatigue_pre', 'baseline_fatigue'])
    has_post = any(var in columns for var in ['post_fatigue', 'fatigue_post', 'end_fatigue'])
    
    if has_pre and has_post:
        return 'paired', "Paired data detected"
    
    # Check for baseline-only data
    baseline_vars = ['baseline_fatigue', 'pre_fatigue', 'fatigue_pre']
    has_baseline = any(var in columns for var in baseline_vars)
    
    if has_baseline:
        return 'baseline', "Baseline data detected"
    
    return 'none', "No fatigue ratings found"

def run_benjamini_hochberg(df, alpha=0.05):
    """
    Apply Benjamini-Hochberg correction to a dataframe of p-values.
    
    Args:
        df: DataFrame with a 'p_value' column
        alpha: Significance threshold (default 0.05)
        
    Returns:
        DataFrame with added 'p_adjusted' and 'significant' columns
    """
    if len(df) == 0:
        return df.copy()
    
    # Sort by p-value
    df_sorted = df.sort_values('p_value').reset_index(drop=True)
    n = len(df_sorted)
    
    # Calculate adjusted p-values
    df_sorted['p_adjusted'] = (df_sorted['p_value'] * n) / (np.arange(1, n + 1))
    
    # Enforce monotonicity (from largest to smallest rank)
    # We need to ensure that adjusted p-values are non-decreasing as p-values increase
    # Actually, we enforce that p_adj[i] <= p_adj[i+1] when sorted by p_value
    # So we iterate backwards and take the minimum
    for i in range(n - 2, -1, -1):
        df_sorted.loc[i, 'p_adjusted'] = min(df_sorted.loc[i, 'p_adjusted'], 
                                             df_sorted.loc[i+1, 'p_adjusted'])
    
    # Cap at 1.0
    df_sorted['p_adjusted'] = df_sorted['p_adjusted'].clip(upper=1.0)
    
    # Determine significance
    df_sorted['significant'] = df_sorted['p_adjusted'] <= alpha
    
    # Restore original order
    return df_sorted.sort_index().reset_index(drop=True)

def run_correlation_analysis(lzc_df, pe_df, metadata_df, mode):
    """
    Run correlation analysis between complexity metrics and fatigue scores.
    
    Args:
        lzc_df: DataFrame with LZC metrics
        pe_df: DataFrame with PE metrics
        metadata_df: DataFrame with fatigue ratings
        mode: 'paired' or 'baseline'
        
    Returns:
        dict: Analysis results
    """
    results = {
        'mode': mode,
        'correlations': []
    }
    
    if mode == 'paired':
        # Identify pre/post columns
        pre_col = next((c for c in metadata_df.columns if c in ['pre_fatigue', 'fatigue_pre', 'baseline_fatigue']), None)
        post_col = next((c for c in metadata_df.columns if c in ['post_fatigue', 'fatigue_post', 'end_fatigue']), None)
        
        if pre_col and post_col:
            metadata_df['fatigue_delta'] = metadata_df[post_col] - metadata_df[pre_col]
            
            # Merge with complexity metrics
            # For simplicity, we'll use the mean complexity across channels for each participant
            lzc_mean = lzc_df.groupby('participant_id')['lzc_value'].mean().reset_index()
            lzc_mean.rename(columns={'lzc_value': 'lzc_mean'}, inplace=True)
            
            pe_mean = pe_df.groupby('participant_id')['pe_value'].mean().reset_index()
            pe_mean.rename(columns={'pe_value': 'pe_mean'}, inplace=True)
            
            merged = metadata_df.merge(lzc_mean, on='participant_id', how='inner')
            merged = merged.merge(pe_mean, on='participant_id', how='inner')
            
            # Calculate correlations
            for metric in ['lzc_mean', 'pe_mean']:
                if len(merged) > 2:
                    corr, p_val = spearmanr(merged[metric], merged['fatigue_delta'])
                    results['correlations'].append({
                        'metric': metric,
                        'correlation': corr,
                        'p_value': p_val,
                        'n': len(merged)
                    })
    
    elif mode == 'baseline':
        baseline_col = next((c for c in metadata_df.columns if c in ['baseline_fatigue', 'pre_fatigue', 'fatigue_pre']), None)
        
        if baseline_col:
            lzc_mean = lzc_df.groupby('participant_id')['lzc_value'].mean().reset_index()
            lzc_mean.rename(columns={'lzc_value': 'lzc_mean'}, inplace=True)
            
            pe_mean = pe_df.groupby('participant_id')['pe_value'].mean().reset_index()
            pe_mean.rename(columns={'pe_value': 'pe_mean'}, inplace=True)
            
            merged = metadata_df.merge(lzc_mean, on='participant_id', how='inner')
            merged = merged.merge(pe_mean, on='participant_id', how='inner')
            
            for metric in ['lzc_mean', 'pe_mean']:
                if len(merged) > 2:
                    corr, p_val = spearmanr(merged[metric], merged[baseline_col])
                    results['correlations'].append({
                        'metric': metric,
                        'correlation': corr,
                        'p_value': p_val,
                        'n': len(merged)
                    })
    
    return results

def calculate_vif(df, feature_cols):
    """
    Calculate Variance Inflation Factor for collinearity diagnostics.
    
    Args:
        df: DataFrame with features
        feature_cols: List of feature column names
        
    Returns:
        dict: VIF values for each feature
    """
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    import statsmodels.api as sm
    
    vif_data = {}
    X = df[feature_cols]
    X = sm.add_constant(X)
    
    for i, col in enumerate(feature_cols):
        vif = variance_inflation_factor(X.values, i + 1)  # +1 because of constant
        vif_data[col] = vif
    
    return vif_data

def main():
    """Main entry point for the analysis pipeline."""
    parser = argparse.ArgumentParser(description='Analyze EEG complexity metrics vs fatigue scores')
    parser.add_argument('--config', type=str, required=True, help='Path to config file')
    args = parser.parse_args()
    
    try:
        config = load_config(args.config)
        logger.info("Configuration loaded successfully")
        
        # Load metadata
        metadata_path = config.get('metadata_path')
        if not metadata_path or not os.path.exists(metadata_path):
            logger.error(f"Metadata file not found: {metadata_path}")
            sys.exit(1)
        
        metadata_df = pd.read_csv(metadata_path)
        logger.info(f"Loaded metadata with {len(metadata_df)} participants")
        
        # Validate metadata for fatigue ratings
        mode, message = validate_metadata(metadata_df)
        logger.info(f"Data mode: {mode} - {message}")
        
        if mode == 'none':
            logger.error("ERROR: No valid fatigue data found. Neither paired (pre/post) nor baseline data is available.")
            logger.error("Please ensure the metadata contains columns for pre/post fatigue ratings or baseline fatigue.")
            
            # Write validation report
            report = {
                "status": "fail",
                "message": "Required fatigue variables missing",
                "available_variables": metadata_df.columns.tolist()
            }
            output_dir = config.get('output_dir', '.')
            os.makedirs(output_dir, exist_ok=True)
            report_path = os.path.join(output_dir, 'validation_report.json')
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            sys.exit(1)
        
        # Load complexity metrics
        lzc_path = config.get('lzc_metrics_path')
        pe_path = config.get('pe_metrics_path')
        
        if not os.path.exists(lzc_path):
            logger.error(f"LZC metrics file not found: {lzc_path}")
            sys.exit(1)
        
        if not os.path.exists(pe_path):
            logger.error(f"PE metrics file not found: {pe_path}")
            sys.exit(1)
        
        lzc_df = pd.read_csv(lzc_path)
        pe_df = pd.read_csv(pe_path)
        logger.info(f"Loaded LZC metrics: {len(lzc_df)} rows, PE metrics: {len(pe_df)} rows")
        
        # Run correlation analysis
        results = run_correlation_analysis(lzc_df, pe_df, metadata_df, mode)
        logger.info(f"Correlation analysis complete. Found {len(results['correlations'])} correlations")
        
        # Apply BH correction if we have p-values
        if results['correlations']:
            p_values_df = pd.DataFrame(results['correlations'])
            if 'p_value' in p_values_df.columns:
                corrected = run_benjamini_hochberg(p_values_df)
                results['corrected'] = corrected.to_dict('records')
                logger.info("Benjamini-Hochberg correction applied")
        
        # Save results
        output_dir = config.get('output_dir', '.')
        os.makedirs(output_dir, exist_ok=True)
        
        results_path = os.path.join(output_dir, 'analysis_results.json')
        with open(results_path, 'w') as f:
            # Convert numpy types to Python types for JSON serialization
            json_results = json.loads(json.dumps(results, default=lambda x: float(x) if isinstance(x, (np.floating, np.integer)) else str(x)))
            json.dump(json_results, f, indent=2)
        
        logger.info(f"Analysis results saved to {results_path}")
        
    except Exception as e:
        logger.exception(f"Pipeline failed: {str(e)}")
        sys.exit(1)

# Import here to avoid circular imports if statsmodels is not installed
from scipy.stats import spearmanr

if __name__ == '__main__':
    main()
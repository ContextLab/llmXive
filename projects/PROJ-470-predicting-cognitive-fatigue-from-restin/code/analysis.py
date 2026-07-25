import os
import sys
import json
import yaml
import pandas as pd
import numpy as np
from pathlib import Path
import logging
from scipy import stats

# Import from existing modules
from utils.logging import get_logger, log_participant_exclusion

def load_config(config_path='code/config.yaml'):
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def setup_logger(name, log_file=None, level=logging.INFO):
    """Set up a logger with file and console handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # File handler
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        fh = logging.FileHandler(log_file)
        fh.setLevel(level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    return logger

def validate_metadata(metadata_df):
    """
    Validate metadata dataframe for required columns.
    
    Args:
        metadata_df: DataFrame containing metadata
        
    Returns:
        Tuple (is_valid, message)
    """
    required_cols = ['participant_id']
    missing = [col for col in required_cols if col not in metadata_df.columns]
    
    if missing:
        return False, f"Missing required columns: {missing}"
    
    # Check for fatigue ratings
    has_pre = any(col in metadata_df.columns for col in ['pre_fatigue', 'fatigue_pre', 'baseline_fatigue'])
    has_post = any(col in metadata_df.columns for col in ['post_fatigue', 'fatigue_post', 'end_fatigue'])
    
    if not has_pre and not has_post:
        return False, "No fatigue rating columns found (pre or post)"
    
    return True, "Metadata validation passed"

def run_correlation_analysis(features_df, metadata_df, mode='paired'):
    """
    Run correlation analysis between complexity metrics and fatigue scores.
    
    Args:
        features_df: DataFrame with complexity metrics
        metadata_df: DataFrame with fatigue ratings
        mode: 'paired' for delta analysis, 'cross_sectional' for baseline analysis
        
    Returns:
        DataFrame with correlation results
    """
    logger = get_logger(__name__)
    
    # Merge features and metadata
    merged = features_df.merge(metadata_df, on='participant_id', how='inner')
    
    if merged.empty:
        logger.error("No overlapping participants between features and metadata.")
        return pd.DataFrame()
    
    # Identify fatigue columns
    pre_cols = [col for col in merged.columns if col in ['pre_fatigue', 'fatigue_pre', 'baseline_fatigue']]
    post_cols = [col for col in merged.columns if col in ['post_fatigue', 'fatigue_post', 'end_fatigue']]
    
    if mode == 'paired':
        if not pre_cols or not post_cols:
            logger.error("Paired mode requires both pre and post fatigue ratings.")
            return pd.DataFrame()
        
        pre_col = pre_cols[0]
        post_col = post_cols[0]
        
        # Calculate deltas
        merged['fatigue_delta'] = merged[post_col] - merged[pre_col]
        merged['complexity_delta'] = merged.groupby('participant_id')['lzc_value'].transform(lambda x: x.max() - x.min()) # Simplified delta
        
        # Filter out NaNs
        valid = merged.dropna(subset=['fatigue_delta', 'complexity_delta'])
        
        if len(valid) < 3:
            logger.error("Insufficient data for paired analysis.")
            return pd.DataFrame()
        
        # Calculate correlation
        corr, p_value = stats.pearsonr(valid['fatigue_delta'], valid['complexity_delta'])
        
        results = pd.DataFrame({
            'correlation_type': ['paired_delta'],
            'r': [corr],
            'p_value': [p_value],
            'n': [len(valid)]
        })
        
    else: # cross_sectional
        if not pre_cols:
            logger.error("Cross-sectional mode requires baseline fatigue ratings.")
            return pd.DataFrame()
        
        base_col = pre_cols[0]
        
        # Filter out NaNs
        valid = merged.dropna(subset=[base_col, 'lzc_value'])
        
        if len(valid) < 3:
            logger.error("Insufficient data for cross-sectional analysis.")
            return pd.DataFrame()
        
        # Calculate correlation
        corr, p_value = stats.pearsonr(valid[base_col], valid['lzc_value'])
        
        results = pd.DataFrame({
            'correlation_type': ['cross_sectional_baseline'],
            'r': [corr],
            'p_value': [p_value],
            'n': [len(valid)]
        })
    
    return results

def run_benjamini_hochberg(p_values, alpha=0.05):
    """
    Apply Benjamini-Hochberg correction for multiple comparisons.
    
    Args:
        p_values: List or array of p-values
        alpha: Significance level
        
    Returns:
        DataFrame with adjusted p-values and significance
    """
    p_values = np.array(p_values)
    n = len(p_values)
    ranks = np.argsort(p_values)
    sorted_p = p_values[ranks]
    
    # BH correction
    adjusted = sorted_p * n / (np.arange(1, n + 1))
    adjusted = np.minimum(adjusted, 1.0)
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1] # Ensure monotonicity
    
    # Map back to original order
    final_adjusted = np.empty(n)
    final_adjusted[ranks] = adjusted
    
    significant = final_adjusted <= alpha
    
    return pd.DataFrame({
        'original_p': p_values,
        'adjusted_p': final_adjusted,
        'significant': significant
    })

def calculate_vif(df, feature_columns):
    """
    Calculate Variance Inflation Factor (VIF) for given features.
    
    Args:
        df: DataFrame containing the data
        feature_columns: List of column names to calculate VIF for
        
    Returns:
        DataFrame with columns: feature, vif
    """
    if len(feature_columns) < 2:
        logging.warning("VIF calculation requires at least 2 features.")
        return pd.DataFrame(columns=['feature', 'vif'])

    X = df[feature_columns].dropna()
    if X.empty:
        logging.warning("No valid data for VIF calculation after dropping NaNs.")
        return pd.DataFrame(columns=['feature', 'vif'])

    # Add intercept
    X_with_intercept = pd.DataFrame({'intercept': 1, **X.to_dict(orient='list')})
    
    vif_data = []
    for col in feature_columns:
        if col not in X_with_intercept.columns:
            continue
        
        try:
            y = X_with_intercept[col]
            X_other = X_with_intercept.drop(columns=[col])
            
            # Check rank
            rank = np.linalg.matrix_rank(X_other.values)
            if rank < X_other.shape[1]:
                vif = np.inf
            else:
                coeffs, residuals, rank, s = np.linalg.lstsq(X_other.values, y, rcond=None)
                y_pred = X_other.values @ coeffs
                
                ss_res = np.sum((y - y_pred) ** 2)
                ss_tot = np.sum((y - np.mean(y)) ** 2)
                
                if ss_tot == 0:
                    r_squared = 0
                else:
                    r_squared = 1 - (ss_res / ss_tot)
                
                vif = 1 / (1 - r_squared) if (1 - r_squared) != 0 else np.inf
            
            vif_data.append({'feature': col, 'vif': vif})
        except Exception as e:
            logging.error(f"Error calculating VIF for {col}: {e}")
            vif_data.append({'feature': col, 'vif': np.nan})

    return pd.DataFrame(vif_data)

def main():
    """Main entry point for analysis pipeline."""
    logging.basicConfig(level=logging.INFO)
    logger = get_logger(__name__)
    
    try:
        config = load_config()
        logger.info("Starting analysis pipeline.")
        
        # Load data (example paths, adjust based on actual data)
        features_path = 'data/processed/lzc_metrics.csv'
        metadata_path = 'data/raw/metadata.csv' # Placeholder, actual path depends on download
        
        if not os.path.exists(features_path):
            logger.error(f"Features file not found: {features_path}")
            sys.exit(1)
        
        features_df = pd.read_csv(features_path)
        
        # Load metadata if exists
        if os.path.exists(metadata_path):
            metadata_df = pd.read_csv(metadata_path)
            is_valid, msg = validate_metadata(metadata_df)
            if not is_valid:
                logger.error(f"Metadata validation failed: {msg}")
                # Write validation report
                report = {'status': 'fail', 'message': msg}
                with open('validation_report.json', 'w') as f:
                    json.dump(report, f)
                sys.exit(1)
        else:
            logger.warning("Metadata file not found. Skipping correlation analysis.")
            sys.exit(0)
        
        # Run correlation analysis
        results = run_correlation_analysis(features_df, metadata_df, mode='paired')
        
        if not results.empty:
            results.to_csv('data/analysis/correlation_results.csv', index=False)
            logger.info("Correlation analysis completed and saved.")
            
            # Apply BH correction if multiple tests
            if len(results) > 1:
                p_vals = results['p_value'].tolist()
                bh_results = run_benjamini_hochberg(p_vals)
                results['adjusted_p'] = bh_results['adjusted_p']
                results['significant'] = bh_results['significant']
                results.to_csv('data/analysis/correlation_results.csv', index=False)
        else:
            logger.warning("No correlation results generated.")
            
    except Exception as e:
        logger.error(f"Analysis pipeline failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
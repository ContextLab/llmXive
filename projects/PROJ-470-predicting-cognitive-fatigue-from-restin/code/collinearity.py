import os
import sys
import json
import yaml
import pandas as pd
import numpy as np
from pathlib import Path
import logging

# Import from existing modules
from utils.logging import get_logger, log_participant_exclusion

def load_config(config_path='code/config.yaml'):
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def load_analysis_results(analysis_dir='data/analysis'):
    """
    Load analysis results from CSV files in the analysis directory.
    Specifically looks for correlation results or feature metrics.
    """
    results = {}
    analysis_path = Path(analysis_dir)
    
    if not analysis_path.exists():
        logging.warning(f"Analysis directory {analysis_dir} does not exist.")
        return results

    for csv_file in analysis_path.glob('*.csv'):
        try:
            df = pd.read_csv(csv_file)
            results[csv_file.stem] = df
        except Exception as e:
            logging.warning(f"Could not load {csv_file}: {e}")
    
    return results

def calculate_vif(df, feature_columns, target_column=None):
    """
    Calculate Variance Inflation Factor (VIF) for given features.
    
    Args:
        df: DataFrame containing the data
        feature_columns: List of column names to calculate VIF for
        target_column: Optional target column (not used for VIF calculation itself)
        
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
        
        # Regress this feature against all other features
        y = X_with_intercept[col]
        X_other = X_with_intercept.drop(columns=[col])
        
        # Fit OLS manually using numpy
        # X_other = X_other.values
        # y = y.values
        
        # Check for perfect multicollinearity (rank deficiency)
        try:
            # Using numpy.linalg.lstsq for regression
            # Add bias term if not already present in X_other for this regression
            # Actually, X_with_intercept already has 'intercept', so X_other includes it
            # We need to solve X_other * beta = y
            
            # Check rank
            rank = np.linalg.matrix_rank(X_other.values)
            if rank < X_other.shape[1]:
                vif = np.inf
            else:
                # R^2 calculation
                # y_pred = np.linalg.lstsq(X_other.values, y, rcond=None)[0]
                # Actually, we need to solve the linear system
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

def run_collinearity_diagnostics(config, analysis_results=None):
    """
    Run collinearity diagnostics on the analysis results.
    
    Args:
        config: Configuration dictionary
        analysis_results: Pre-loaded analysis results (optional)
        
    Returns:
        DataFrame with VIF values
    """
    logger = get_logger(__name__)
    
    if analysis_results is None:
        analysis_results = load_analysis_results()
    
    # Determine which features to check
    # Typically we check the complexity metrics (LZC, PE) if they are combined
    # We look for files like 'correlation_results.csv' or merged feature files
    
    vif_results = pd.DataFrame()
    
    # Try to find a combined feature set or correlation results
    # If 'correlation_results' exists, it might have the features we need
    if 'correlation_results' in analysis_results:
        df = analysis_results['correlation_results']
        # Identify feature columns (exclude participant_id, etc.)
        feature_cols = [col for col in df.columns if col not in ['participant_id', 'subject_id', 'channel', 'threshold', 'count_significant', 'vif']]
        
        # We need at least 2 features to calculate VIF
        if len(feature_cols) >= 2:
            vif_results = calculate_vif(df, feature_cols)
            logger.info(f"Calculated VIF for {len(feature_cols)} features.")
        else:
            logger.warning(f"Not enough features ({len(feature_cols)}) to calculate VIF.")
    else:
        # Fallback: check for merged feature files
        for key, df in analysis_results.items():
            feature_cols = [col for col in df.columns if col not in ['participant_id', 'subject_id', 'channel', 'threshold', 'count_significant', 'vif']]
            if len(feature_cols) >= 2:
                vif_results = calculate_vif(df, feature_cols)
                logger.info(f"Calculated VIF for {len(feature_cols)} features from {key}.")
                break
        
        if vif_results.empty:
            logger.warning("No suitable data found for VIF calculation.")

    return vif_results

def save_collinearity_report(vif_results, output_path='data/analysis/vif_report.csv'):
    """
    Save VIF results to CSV.
    
    Args:
        vif_results: DataFrame with VIF values
        output_path: Path to save the report
    """
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    vif_results.to_csv(output_path, index=False)
    logging.info(f"VIF report saved to {output_path}")

def main():
    """Main entry point for collinearity diagnostics."""
    logging.basicConfig(level=logging.INFO)
    logger = get_logger(__name__)
    
    try:
        config = load_config()
        logger.info("Starting collinearity diagnostics.")
        
        vif_results = run_collinearity_diagnostics(config)
        
        if not vif_results.empty:
            save_collinearity_report(vif_results)
            
            # Check for high VIF values
            high_vif = vif_results[vif_results['vif'] >= 5]
            if not high_vif.empty:
                logger.warning(f"High VIF detected for {len(high_vif)} features: {high_vif['feature'].tolist()}")
                logger.warning("Consider removing features with VIF >= 5 to reduce multicollinearity.")
            else:
                logger.info("All VIF values are below 5. No significant multicollinearity detected.")
        else:
            logger.warning("No VIF results to report.")
            
    except Exception as e:
        logger.error(f"Collinearity diagnostics failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

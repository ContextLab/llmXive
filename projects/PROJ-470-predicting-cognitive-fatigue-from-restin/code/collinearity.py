"""
Collinearity diagnostics module for VIF calculation.
Implements SC-004: Variance Inflation Factor (VIF) < 5 constraint.
"""
import os
import sys
import json
import yaml
import pandas as pd
import numpy as np
from pathlib import Path
import logging
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Import existing utilities from project structure
from utils.logging import get_logger

def load_config(config_path="code/config.yaml"):
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def setup_logger(name, log_file="data/analysis/collinearity.log"):
    """Setup logger for collinearity diagnostics."""
    logger = get_logger(name, log_file)
    return logger

def load_analysis_results(metrics_dir="data/processed"):
    """
    Load Lempel-Ziv Complexity and Permutation Entropy metrics.
    Returns a combined DataFrame of predictors.
    """
    lzc_path = os.path.join(metrics_dir, "lzc_metrics.csv")
    pe_path = os.path.join(metrics_dir, "pe_metrics.csv")
    
    if not os.path.exists(lzc_path):
        raise FileNotFoundError(f"Required file missing: {lzc_path}")
    if not os.path.exists(pe_path):
        raise FileNotFoundError(f"Required file missing: {pe_path}")
        
    lzc_df = pd.read_csv(lzc_path)
    pe_df = pd.read_csv(pe_path)
    
    # Ensure consistent participant_id column name if necessary
    if 'participant_id' not in lzc_df.columns:
        # Try to find a suitable ID column or fail
        raise ValueError(f"lzc_metrics.csv missing 'participant_id' column. Columns: {lzc_df.columns.tolist()}")
    
    # Merge on participant_id to create the combined predictor set
    # Assuming both files have 'participant_id' and channel-specific columns
    # We need to align them. If channels differ, we might need to handle that,
    # but for VIF we assume the same set of features per participant.
    # Let's assume the structure is: participant_id, channel_1, channel_2, ...
    
    # Merge
    combined = pd.merge(lzc_df, pe_df, on='participant_id', suffixes=('_lzc', '_pe'))
    
    # Identify predictor columns (exclude participant_id and any non-numeric)
    predictor_cols = combined.select_dtypes(include=[np.number]).columns.tolist()
    if 'participant_id' in predictor_cols:
        predictor_cols.remove('participant_id')
        
    if len(predictor_cols) == 0:
        raise ValueError("No numeric predictor columns found in merged metrics.")
        
    return combined, predictor_cols

def calculate_vif(data, predictors):
    """
    Calculate Variance Inflation Factor for each predictor.
    
    Args:
        data: DataFrame containing predictor variables
        predictors: List of column names to calculate VIF for
        
    Returns:
        DataFrame with columns: ['predictor', 'vif']
    """
    X = data[predictors]
    
    # Add constant for intercept if needed (statsmodels VIF usually expects it)
    # However, vif function in statsmodels.stats.outliers_influence 
    # calculates VIF for each column in X. 
    # Standard VIF formula: 1 / (1 - R^2_j) where R^2_j is from regressing X_j on other Xs.
    
    vif_data = []
    for i, col in enumerate(predictors):
        # Calculate VIF for this column
        # Using the standard approach: regress col on all other predictors
        y = X[col]
        X_other = X.drop(columns=[col])
        
        # If X_other is empty (only 1 predictor), VIF is undefined or 1
        if X_other.empty:
            vif_val = 1.0
        else:
            # Add constant for the regression
            try:
                from sklearn.linear_model import LinearRegression
                reg = LinearRegression().fit(X_other, y)
                r_squared = reg.score(X_other, y)
                if r_squared >= 1.0:
                    vif_val = np.inf
                else:
                    vif_val = 1.0 / (1.0 - r_squared)
            except Exception as e:
                logging.error(f"Error calculating VIF for {col}: {e}")
                vif_val = np.inf
        
        vif_data.append({'predictor': col, 'vif': vif_val})
        
    return pd.DataFrame(vif_data)

def run_collinearity_diagnostics(config=None):
    """
    Run full collinearity diagnostics pipeline.
    
    Returns:
        Tuple (vif_df, is_valid) where is_valid is True if all VIF < 5
    """
    logger = setup_logger("collinearity")
    logger.info("Starting collinearity diagnostics (VIF calculation)")
    
    if config is None:
        config = load_config()
    
    try:
        df, predictors = load_analysis_results()
        logger.info(f"Loaded {len(df)} participants with {len(predictors)} predictors")
        
        vif_df = calculate_vif(df, predictors)
        
        # Log results
        logger.info("VIF Results:")
        for _, row in vif_df.iterrows():
            logger.info(f"  {row['predictor']}: VIF = {row['vif']:.4f}")
        
        # Check constraint: VIF < 5
        max_vif = vif_df['vif'].max()
        is_valid = max_vif < 5.0
        
        if not is_valid:
            failed_predictors = vif_df[vif_df['vif'] >= 5.0]['predictor'].tolist()
            error_msg = (
                f"Collinearity constraint violated (SC-004). "
                f"Max VIF = {max_vif:.4f}. "
                f"Predictors with VIF >= 5: {failed_predictors}. "
                f"Model assumptions invalid. Exiting."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("Collinearity diagnostics passed. All VIF < 5.")
        return vif_df, True
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during diagnostics: {e}")
        raise

def save_collinearity_report(vif_df, output_path="data/analysis/vif_diagnostics.csv"):
    """
    Save VIF diagnostics to CSV.
    
    Args:
        vif_df: DataFrame with 'predictor' and 'vif' columns
        output_path: Path to save the CSV
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    vif_df.to_csv(output_path, index=False)
    logging.info(f"VIF diagnostics saved to {output_path}")

def main():
    """Main entry point for collinearity diagnostics."""
    logger = setup_logger("collinearity")
    logger.info("=== Collinearity Diagnostics (T037) ===")
    
    try:
        vif_df, is_valid = run_collinearity_diagnostics()
        save_collinearity_report(vif_df)
        logger.info("Task T037 completed successfully.")
        sys.exit(0)
        
    except FileNotFoundError as e:
        logger.error(f"Critical file missing: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Collinearity check failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

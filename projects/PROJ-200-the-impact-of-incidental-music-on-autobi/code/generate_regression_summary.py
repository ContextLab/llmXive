import os
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import sys

# Add project root to path if not already present
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_project_root, get_config_dict
from utils import setup_logging, get_logger
from state_manager import save_state, calculate_checksum
from modeling import load_user_track_pairs, fit_mixed_model

logger = get_logger(__name__)

def load_regression_results() -> pd.DataFrame:
    """
    Load the fitted model results.
    
    Since the model is fit in-memory in modeling.py, we need to re-fit
    or retrieve the results. For this implementation, we re-fit the model
    on the user_track_pairs data to extract the summary statistics.
    
    Returns:
        pd.DataFrame: Model summary statistics.
    """
    logger.info("Loading user track pairs data...")
    pairs_path = get_project_root() / "data" / "processed" / "user_track_pairs.parquet"
    
    if not pairs_path.exists():
        raise FileNotFoundError(f"Required input file not found: {pairs_path}")
    
    df = pd.read_parquet(pairs_path)
    logger.info(f"Loaded {len(df)} user-track pairs")
    
    logger.info("Fitting mixed effects model...")
    model = fit_mixed_model(df)
    
    return model

def calculate_vif(model) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for model predictors.
    
    Args:
        model: Fitted statsmodels MixedLM model.
        
    Returns:
        Dict[str, float]: VIF values for each predictor.
    """
    # Get the design matrix from the model
    # For MixedLM, we need to extract the fixed effects design matrix
    try:
        # Access the design matrix if available
        if hasattr(model, 'formula') and hasattr(model, 'model'):
            # Extract exog from the underlying model
            exog = model.model.exog
            col_names = model.model.exog_names
        else:
            # Fallback: try to get from the result object
            exog = model.exog
            col_names = model.exog_names
        
        # Remove intercept column if present (first column is usually all 1s)
        if exog.shape[1] > 1 and np.allclose(exog[:, 0], 1):
            exog = exog[:, 1:]
            col_names = col_names[1:]
        
        vif_dict = {}
        for i, name in enumerate(col_names):
            # Calculate VIF: 1 / (1 - R^2) where R^2 is from regressing
            # column i on all other columns
            X_other = np.delete(exog, i, axis=1)
            X_i = exog[:, i]
            
            # Simple linear regression to get R^2
            # X_i = beta_0 + beta_1 * X_other + error
            try:
                # Add intercept for regression
                X_other_const = np.column_stack([np.ones(len(X_i)), X_other])
                betas, _, _, _ = np.linalg.lstsq(X_other_const, X_i, rcond=None)
                predicted = X_other_const @ betas
                ss_res = np.sum((X_i - predicted) ** 2)
                ss_tot = np.sum((X_i - np.mean(X_i)) ** 2)
                r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
                
                vif = 1.0 / (1 - r_squared) if r_squared < 1 else np.inf
                vif_dict[name] = vif
            except Exception as e:
                logger.warning(f"Could not calculate VIF for {name}: {e}")
                vif_dict[name] = np.nan
        
        return vif_dict
    except Exception as e:
        logger.error(f"Error calculating VIF: {e}")
        return {}

def generate_summary_dataframe(model, vif_dict: Dict[str, float]) -> pd.DataFrame:
    """
    Generate a summary dataframe with coefficients, SEs, p-values, and VIFs.
    
    Args:
        model: Fitted statsmodels MixedLM model.
        vif_dict: Dictionary of VIF values.
        
    Returns:
        pd.DataFrame: Summary table.
    """
    # Extract fixed effects results
    params = model.params
    std_err = model.bse
    t_values = model.tvalues
    
    # Calculate p-values (two-tailed)
    from scipy import stats
    degrees_of_freedom = model.df_resid
    p_values = 2 * (1 - stats.t.cdf(np.abs(t_values), degrees_of_freedom))
    
    # Create summary dataframe
    summary_data = []
    for name in params.index:
        # Get VIF if available, else NaN
        vif_val = vif_dict.get(name, np.nan)
        
        summary_data.append({
            'variable': name,
            'coefficient': params[name],
            'std_error': std_err[name],
            't_statistic': t_values[name],
            'p_value': p_values[name],
            'vif': vif_val
        })
    
    summary_df = pd.DataFrame(summary_data)
    return summary_df

def main():
    """
    Main function to generate regression summary CSV.
    """
    setup_logging()
    logger.info("Starting regression summary generation (T038)...")
    
    try:
        # Load and fit model
        model = load_regression_results()
        
        # Calculate VIFs
        logger.info("Calculating VIFs...")
        vif_dict = calculate_vif(model)
        
        # Generate summary dataframe
        logger.info("Generating summary dataframe...")
        summary_df = generate_summary_dataframe(model, vif_dict)
        
        # Define output path
        output_dir = get_project_root() / "data" / "final"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "regression_summary.csv"
        
        # Save to CSV
        logger.info(f"Saving summary to {output_path}")
        summary_df.to_csv(output_path, index=False)
        
        # Update state.yaml
        logger.info("Updating state.yaml...")
        checksum = calculate_checksum(output_path)
        save_state(
            file_path=str(output_path.relative_to(get_project_root())),
            checksum=checksum,
            task_id="T038",
            description="Regression summary with coefficients, SEs, p-values, and VIFs"
        )
        
        logger.info("Regression summary generation completed successfully.")
        print(f"Output written to: {output_path}")
        
    except Exception as e:
        logger.error(f"Error generating regression summary: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()

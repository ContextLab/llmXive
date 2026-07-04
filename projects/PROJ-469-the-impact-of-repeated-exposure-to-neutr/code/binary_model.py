"""
Binary Model Fit (Task T024b)

Re-fits the linear regression model using a binary version of political ideology
(median split) instead of the continuous variable.
Results are saved to results/binary_model.csv.
"""
import os
import numpy as np
import pandas as pd
import statsmodels.api as sm
import logging
from pathlib import Path
from typing import Dict, Any

# Import from existing project modules
from config import ensure_dirs
from config_manager import get_results_path, get_data_processed_path, get_config
from logging_config import get_logger
from preprocessing import derive_variables

logger = get_logger(__name__)

def fit_binary_model(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Fits a linear regression model: IAT_D_score ~ news_exposure_z * ideology_binary
    
    Args:
        df: Preprocessed DataFrame containing derived variables.
        
    Returns:
        Dictionary containing model results (coefficients, p-values, etc.)
    """
    logger.info("Fitting binary ideology model...")
    
    # Ensure required columns exist
    required_cols = ['IAT_D_score', 'news_exposure_z', 'ideology_binary']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns for binary model: {missing}")
    
    # Drop rows with missing values in these columns
    model_df = df.dropna(subset=required_cols)
    logger.info(f"Model dataset size after dropping NaNs: {len(model_df)}")
    
    if len(model_df) < 10:
        raise ValueError("Insufficient data points for model fitting after dropping NaNs.")
    
    # Define formula
    formula = "IAT_D_score ~ news_exposure_z * ideology_binary"
    
    # Fit OLS model
    model = sm.formula.ols(formula=formula, data=model_df)
    results = model.fit()
    
    # Extract key metrics
    coef_data = results.params
    p_values = results.pvalues
    
    result_dict = {
        "model_type": "binary_ideology_ols",
        "n_obs": len(model_df),
        "r_squared": results.rsquared,
        "adj_r_squared": results.rsquared_adj,
        "f_statistic": results.fvalue,
        "f_pvalue": results.f_pvalue,
        # Interaction term specifically
        "interaction_coef": coef_data.get('news_exposure_z:ideology_binary', np.nan),
        "interaction_pvalue": p_values.get('news_exposure_z:ideology_binary', np.nan),
        "news_exposure_coef": coef_data.get('news_exposure_z', np.nan),
        "news_exposure_pvalue": p_values.get('news_exposure_z', np.nan),
        "ideology_binary_coef": coef_data.get('ideology_binary', np.nan),
        "ideology_binary_pvalue": p_values.get('ideology_binary', np.nan),
        "intercept": coef_data.get('Intercept', np.nan),
        "intercept_pvalue": p_values.get('Intercept', np.nan)
    }
    
    logger.info(f"Binary model fitted. Interaction p-value: {result_dict['interaction_pvalue']:.4f}")
    return result_dict

def save_binary_model_results(results_dict: Dict[str, Any], output_path: Path) -> None:
    """
    Saves the binary model results to a CSV file.
    
    Args:
        results_dict: Dictionary of model results.
        output_path: Path to save the CSV file.
    """
    # Convert to DataFrame for easy CSV export
    df = pd.DataFrame([results_dict])
    df.to_csv(output_path, index=False)
    logger.info(f"Binary model results saved to {output_path}")

def run_binary_model_pipeline() -> Dict[str, Any]:
    """
    Main pipeline function to load data, fit the binary model, and save results.
    """
    logger.info("Starting Binary Model Fit pipeline (T024b)...")
    
    # Ensure output directory exists
    results_dir = get_results_path()
    ensure_dirs(results_dir)
    output_path = results_dir / "binary_model.csv"
    
    # Load processed data
    processed_data_path = get_data_processed_path()
    if not processed_data_path.exists():
        # If processed data doesn't exist, try to load raw and run preprocessing
        # This handles cases where the pipeline hasn't run fully yet
        logger.warning("Processed data not found. Attempting to load raw and preprocess.")
        # Note: In a strict pipeline, we might fail here, but for robustness we attempt derivation
        # We assume load_project_implicit_data is available in data_loader if needed
        from data_loader import load_project_implicit_data
        raw_df = load_project_implicit_data()
        if raw_df is not None:
            # Run derivation if not already done
            # We need to ensure 'ideology_binary' is derived. 
            # The derive_variables function in preprocessing.py handles this if called.
            # Assuming the data loaded here is raw or partially processed.
            # For safety, we call derive_variables which adds the binary split if missing.
            final_df = derive_variables(raw_df)
        else:
            raise FileNotFoundError("Could not load raw data to derive variables.")
    else:
        df = pd.read_csv(processed_data_path)
        # Check if derived variables exist; if not, try to derive them
        if 'ideology_binary' not in df.columns:
            logger.info("Derived variables missing in processed data, running derivation.")
            df = derive_variables(df)
        final_df = df
    
    # Fit model
    results = fit_binary_model(final_df)
    
    # Save results
    save_binary_model_results(results, output_path)
    
    logger.info("Binary Model Fit pipeline completed successfully.")
    return results

if __name__ == "__main__":
    run_binary_model_pipeline()

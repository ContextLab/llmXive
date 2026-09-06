import os
import numpy as np
import pandas as pd
import statsmodels.api as sm
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from config_manager import get_results_path, get_config
from preprocessing import load_data, impute_mice, derive_variables
from logging_config import get_logger

def fit_binary_model(data: pd.DataFrame) -> sm.OLSResults:
    """
    Fit a linear regression model using the binary ideology variable.
    
    Model: IAT_D_score ~ news_exposure_z + ideology_binary + news_exposure_z:ideology_binary
    
    Parameters
    ----------
    data : pd.DataFrame
        Preprocessed dataframe containing derived variables:
        - IAT_D_score
        - news_exposure_z
        - ideology_binary
    
    Returns
    -------
    sm.OLSResults
        Fitted model results object.
    
    Raises
    ------
    ValueError
        If required columns are missing from the dataframe.
    """
    required_cols = ['IAT_D_score', 'news_exposure_z', 'ideology_binary']
    missing = [col for col in required_cols if col not in data.columns]
    if missing:
        raise ValueError(f"Missing required columns for binary model: {missing}")
    
    # Drop rows with NaN in relevant columns
    model_data = data.dropna(subset=required_cols)
    
    if len(model_data) == 0:
        raise ValueError("No valid data remaining after dropping NaNs for binary model.")
    
    # Create interaction term
    model_data['interaction'] = model_data['news_exposure_z'] * model_data['ideology_binary']
    
    # Define features and target
    features = ['news_exposure_z', 'ideology_binary', 'interaction']
    X = model_data[features]
    y = model_data['IAT_D_score']
    
    # Add constant
    X = sm.add_constant(X)
    
    # Fit model
    model = sm.OLS(y, X).fit()
    
    logger = get_logger(__name__)
    logger.info(f"Binary model fitted on {len(model_data)} observations.")
    logger.info(f"Interaction coefficient: {model.params['interaction']:.4f}, p-value: {model.pvalues['interaction']:.4f}")
    
    return model

def save_binary_model_results(model: sm.OLSResults, output_path: Path) -> Dict[str, Any]:
    """
    Save the binary model results to a CSV file.
    
    Parameters
    ----------
    model : sm.OLSResults
        Fitted model results.
    output_path : Path
        Path to save the CSV results.
    
    Returns
    -------
    Dict[str, Any]
        Dictionary containing the saved results summary.
    """
    results_summary = []
    
    for param_name, param_value in model.params.items():
        results_summary.append({
            'term': param_name,
            'coefficient': param_value,
            'std_err': model.bse[param_name],
            't_value': model.tvalues[param_name],
            'p_value': model.pvalues[param_name],
            'conf_int_lower': model.conf_int().loc[param_name, 0],
            'conf_int_upper': model.conf_int().loc[param_name, 1]
        })
    
    df_results = pd.DataFrame(results_summary)
    
    # Add overall model stats
    overall_stats = {
        'term': 'model_summary',
        'coefficient': model.rsquared,
        'std_err': np.nan,
        't_value': np.nan,
        'p_value': model.f_pvalue,
        'conf_int_lower': np.nan,
        'conf_int_upper': np.nan
    }
    # Append as a separate row or handle differently if needed. 
    # For simplicity, we'll just save the parameter table and add a separate row for summary if needed.
    # But the task asks for "results (coefficient/significance)".
    # Let's create a summary row for the interaction term specifically.
    
    interaction_row = df_results[df_results['term'] == 'interaction'].iloc[0] if 'interaction' in df_results['term'].values else None
    
    if interaction_row is not None:
        interaction_dict = interaction_row.to_dict()
        interaction_dict['term'] = 'interaction_result'
        interaction_dict['coefficient'] = interaction_dict['coefficient']
        interaction_dict['significance'] = interaction_dict['p_value'] < 0.05
        # Save this specific interaction result clearly
        df_interaction = pd.DataFrame([interaction_dict])
        df_interaction.to_csv(output_path, index=False)
    else:
        df_results.to_csv(output_path, index=False)
        
    logger = get_logger(__name__)
    logger.info(f"Binary model results saved to {output_path}")
    
    return interaction_dict if interaction_row is not None else {}

def run_binary_model_pipeline() -> Dict[str, Any]:
    """
    Run the full binary model pipeline:
    1. Load data
    2. Impute missing values (MICE)
    3. Derive variables (including ideology_binary)
    4. Fit binary model
    5. Save results
    
    Returns
    -------
    Dict[str, Any]
        Final results dictionary.
    """
    logger = get_logger(__name__)
    logger.info("Starting binary model pipeline...")
    
    # Load and preprocess
    raw_data = load_data()
    imputed_data = impute_mice(raw_data)
    processed_data = derive_variables(imputed_data)
    
    # Fit model
    model = fit_binary_model(processed_data)
    
    # Save results
    output_path = get_results_path('binary_model.csv')
    results = save_binary_model_results(model, output_path)
    
    logger.info("Binary model pipeline completed successfully.")
    return results

if __name__ == "__main__":
    run_binary_model_pipeline()

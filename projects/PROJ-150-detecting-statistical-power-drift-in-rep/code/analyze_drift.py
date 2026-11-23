import os
import sys
import json
import pickle
import logging
from pathlib import Path
import pandas as pd
import numpy as np
from statsmodels.formula.api import mixedlm
from statsmodels.regression.mixed_linear_model import MixedLMResults
from logging_config import get_module_logger, log_operation_start, log_operation_complete, log_row_skip

def load_models(models_path):
    """Load the full model from pickle."""
    if not os.path.exists(models_path):
        raise FileNotFoundError(f"Full model file not found: {models_path}")
    with open(models_path, 'rb') as f:
        return pickle.load(f)

def get_data_for_reduced_model(input_path):
    """Load and prepare data for the reduced model."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    df = pd.read_csv(input_path)
    
    # Filter out any remaining NaNs in critical columns just in case
    df = df.dropna(subset=['power_est', 'effect_size', 'sample_size', 'field', 'original_study_id'])
    
    # Handle zero-variance fields if they exist (though dropna handles NaNs)
    # If a field has only one unique value, it might cause issues in some models,
    # but MixedLM usually handles single-level groups by treating them as fixed or dropping.
    # We'll ensure 'field' and 'original_study_id' are categorical strings.
    df['field'] = df['field'].astype(str)
    df['original_study_id'] = df['original_study_id'].astype(str)
    
    return df

def fit_reduced_model(df, logger):
    """
    Fit the reduced model: power_est ~ effect_size + sample_size + (1|field) + (1|original_study_id)
    Excludes 'year' as per T013a.
    """
    formula = "power_est ~ effect_size + sample_size"
    groups_field = df['field']
    groups_study = df['original_study_id']
    
    # We need to handle the random effects structure carefully.
    # statsmodels MixedLM allows one grouping variable. To have two, we often
    # nest them or use a specific formula. However, the standard way in statsmodels
    # for multiple random intercepts is not direct in the formula string.
    # A common workaround is to create a composite group key or use the `vc_formula` argument.
    # Given the spec requirement for (1|field) + (1|original_study_id), we use `vc_formula`.
    
    # Define random effects: (1|field) and (1|original_study_id)
    # We pass the main grouping variable (e.g., original_study_id) and use vc_formula for the other.
    # However, if we want both to be random intercepts, we can try:
    # group = df['original_study_id']
    # re_formula = "1"
    # vc_formula = {"field": "1"}
    
    # Let's try the standard approach for multiple random intercepts in statsmodels:
    # Use one as the main group, and the other in vc_formula.
    group_var = df['original_study_id']
    re_formula = "1"
    vc_formula = {"field": "1"}
    
    try:
        model = mixedlm(formula, df, groups=group_var, re_formula=re_formula, vc_formula=vc_formula)
        result = model.fit()
        return result
    except Exception as e:
        logger.error(f"Failed to fit reduced model: {str(e)}")
        raise

def perform_lrt(full_model, reduced_model, logger):
    """
    Perform Likelihood-Ratio Test comparing full vs reduced model.
    """
    # statsmodels MixedLMResults has a method for LRT?
    # Actually, we can compute it manually: chi2 = 2 * (ll_full - ll_reduced)
    # df_diff = df_full - df_reduced
    
    ll_full = full_model.llf
    ll_reduced = reduced_model.llf
    
    if ll_full is None or ll_reduced is None:
        raise ValueError("Log-likelihoods are None. Models may not have converged.")
    
    chi2_stat = 2 * (ll_full - ll_reduced)
    df_diff = full_model.df_model - reduced_model.df_model
    
    # P-value from chi2 distribution
    from scipy import stats
    p_value = stats.chi2.sf(chi2_stat, df_diff)
    
    return {
        "chi2_statistic": float(chi2_stat),
        "df_diff": int(df_diff),
        "p_value": float(p_value)
    }

def save_results(results, output_path, logger):
    """Save LRT results to JSON."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"LRT results saved to {output_path}")

def main():
    """
    Main entry point for analyzing drift (LRT).
    """
    logger = get_module_logger(__name__)
    log_operation_start(logger, "Drift Analysis (LRT)")
    
    # Paths
    full_model_path = "data/derived/input_trends_models.pkl"
    input_data_path = "data/derived/power_estimates.csv"
    reduced_model_path = "data/derived/reduced_model.pkl"
    lrt_output_path = "data/derived/lrt_results.json"
    
    try:
        # Load full model
        logger.info("Loading full model")
        full_model = load_models(full_model_path)
        
        # Load data for reduced model
        logger.info("Loading data for reduced model")
        df = get_data_for_reduced_model(input_data_path)
        
        # Fit reduced model
        logger.info("Fitting reduced model")
        reduced_model = fit_reduced_model(df, logger)
        
        # Save reduced model
        Path(reduced_model_path).parent.mkdir(parents=True, exist_ok=True)
        with open(reduced_model_path, 'wb') as f:
            pickle.dump(reduced_model, f)
        logger.info(f"Reduced model saved to {reduced_model_path}")
        
        # Perform LRT
        logger.info("Performing Likelihood-Ratio Test")
        lrt_results = perform_lrt(full_model, reduced_model, logger)
        
        # Save results
        save_results(lrt_results, lrt_output_path, logger)
        
        log_operation_complete(logger, "Drift Analysis (LRT)")
        
    except Exception as e:
        logger.error(f"Drift analysis failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()

"""
Statistical models for the Political News Exposure study.

Implements the primary linear regression model:
IAT_D_score ~ news_exposure_z * political_ideology
"""
import os
import numpy as np
import pandas as pd
import statsmodels.api as sm
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from config_manager import get_results_path, get_analysis_seed
from logging_config import get_logger
from config import ensure_dirs

logger = get_logger(__name__)

def fit_primary_model(
    df: pd.DataFrame,
    seed: Optional[int] = None
) -> Tuple[sm.RegressionResultsWrapper, Dict[str, Any]]:
    """
    Fit the primary linear regression model with interaction.
    
    Model: IAT_D_score ~ news_exposure_z * political_ideology
    
    Args:
        df: DataFrame containing preprocessed data with columns:
            - 'IAT_D_score': Dependent variable
            - 'news_exposure_z': Z-scored news exposure frequency
            - 'political_ideology': Continuous political ideology score
        seed: Random seed for reproducibility (used if needed for any stochastic steps)
        
    Returns:
        Tuple of (model_results, diagnostics_dict)
        - model_results: statsmodels RegressionResults object
        - diagnostics_dict: Dictionary with model metrics and metadata
    
    Raises:
        ValueError: If required columns are missing
        RuntimeError: If model fitting fails
    """
    if seed is not None:
        np.random.seed(seed)
    
    required_cols = ['IAT_D_score', 'news_exposure_z', 'political_ideology']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns for primary model: {missing_cols}")
    
    # Drop rows with missing values in required columns
    clean_df = df.dropna(subset=required_cols)
    n_dropped = len(df) - len(clean_df)
    if n_dropped > 0:
        logger.warning(f"Dropped {n_dropped} rows due to missing values in model variables")
    
    if len(clean_df) < 10:
        raise RuntimeError(f"Insufficient data for model fitting after dropping missing values: n={len(clean_df)}")
    
    # Prepare features with interaction term
    # Using statsmodels formula API for clarity and automatic interaction handling
    formula = "IAT_D_score ~ news_exposure_z * political_ideology"
    
    try:
        model = sm.formula.ols(formula=formula, data=clean_df)
        results = model.fit()
    except Exception as e:
        raise RuntimeError(f"Failed to fit primary linear regression model: {str(e)}")
    
    # Extract key metrics
    diagnostics = {
        "n_observations": int(results.nobs),
        "r_squared": float(results.rsquared),
        "r_squared_adj": float(results.rsquared_adj),
        "f_statistic": float(results.fvalue),
        "f_pvalue": float(results.f_pvalue),
        "interaction_coef": float(results.params['news_exposure_z:political_ideology']),
        "interaction_se": float(results.bse['news_exposure_z:political_ideology']),
        "interaction_t": float(results.tvalues['news_exposure_z:political_ideology']),
        "interaction_p": float(results.pvalues['news_exposure_z:political_ideology']),
        "news_exposure_z_coef": float(results.params['news_exposure_z']),
        "political_ideology_coef": float(results.params['political_ideology']),
        "intercept": float(results.params['Intercept']),
        "aic": float(results.aic),
        "bic": float(results.bic),
        "formula": formula
    }
    
    logger.info(f"Primary model fitted successfully. Interaction p-value: {diagnostics['interaction_p']:.4f}")
    
    return results, diagnostics

def save_model_results(
    results: sm.RegressionResultsWrapper,
    diagnostics: Dict[str, Any],
    output_path: Optional[Path] = None
) -> Path:
    """
    Save model results and diagnostics to CSV.
    
    Args:
        results: statsmodels RegressionResults object
        diagnostics: Dictionary with model metrics
        output_path: Optional path for output file. If None, uses default results path.
        
    Returns:
        Path to the saved CSV file
    """
    if output_path is None:
        output_path = get_results_path() / "primary_model_results.csv"
    
    ensure_dirs(output_path.parent)
    
    # Convert results to DataFrame for CSV export
    summary_df = pd.DataFrame({
        "parameter": results.params.index.tolist(),
        "coefficient": results.params.values,
        "std_error": results.bse.values,
        "t_statistic": results.tvalues.values,
        "p_value": results.pvalues.values,
        "conf_int_lower": results.conf_int()[0].values,
        "conf_int_upper": results.conf_int()[1].values
    })
    
    # Save parameter estimates
    summary_df.to_csv(output_path, index=False)
    
    # Save high-level diagnostics as a separate row
    diag_path = get_results_path() / "primary_model_diagnostics.csv"
    diag_df = pd.DataFrame([diagnostics])
    diag_df.to_csv(diag_path, index=False)
    
    logger.info(f"Model results saved to {output_path}")
    logger.info(f"Model diagnostics saved to {diag_path}")
    
    return output_path

def run_primary_analysis(
    df: pd.DataFrame,
    seed: Optional[int] = None,
    save_results: bool = True
) -> Tuple[sm.RegressionResultsWrapper, Dict[str, Any], Optional[Path]]:
    """
    Run the complete primary analysis pipeline.
    
    Args:
        df: Preprocessed DataFrame
        seed: Random seed
        save_results: Whether to save results to disk
        
    Returns:
        Tuple of (results, diagnostics, output_path)
        - output_path is None if save_results is False
    """
    logger.info("Starting primary model analysis")
    
    results, diagnostics = fit_primary_model(df, seed=seed)
    
    output_path = None
    if save_results:
        output_path = save_model_results(results, diagnostics)
    
    return results, diagnostics, output_path
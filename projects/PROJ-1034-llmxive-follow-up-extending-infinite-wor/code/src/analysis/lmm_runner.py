"""
Linear Mixed-Effects Model Runner (T020, T019 dependency).

This module provides functionality to run Linear Mixed-Effects (LMM) analysis
on simulation data using statsmodels. It handles data preparation, model fitting,
and result extraction.
"""
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, Optional, Union
import statsmodels.formula.api as smf
from statsmodels.regression.mixed_linear_model import MixedLM
import re

logger = logging.getLogger(__name__)

def run_lmm_analysis(
    df: pd.DataFrame,
    formula: str,
    groups_col: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run a Linear Mixed-Effects Model analysis on the provided DataFrame.
    
    Args:
        df (pd.DataFrame): The input data containing the variables in the formula.
        formula (str): The formula string for the LMM (e.g., "y ~ x + (1|group)").
        groups_col (Optional[str]): Explicitly specify the grouping column if 
                                    the formula syntax doesn't resolve it automatically.
    
    Returns:
        Dict[str, Any]: A dictionary containing:
            - 'converged': bool indicating if the model converged.
            - 'params': dict of parameter estimates (if converged).
            - 'fixed_effects': dict of fixed effect coefficients.
            - 'random_effects': dict of random effect variances.
            - 'error': str containing error message if fitting failed.
    """
    logger.info(f"Running LMM analysis with formula: {formula}")
    
    if df is None or df.empty:
        return {
            "converged": False,
            "error": "Input DataFrame is empty or None"
        }
    
    if df.isnull().any().any():
        logger.warning("Input data contains NaN values. Dropping rows with NaN.")
        df_clean = df.dropna()
        if df_clean.empty:
            return {
                "converged": False,
                "error": "All rows dropped due to NaN values"
            }
        df = df_clean
    
    try:
        match = re.search(r'\(1\|([^)]+)\)', formula)
        group_var = match.group(1) if match else groups_col
        
        if group_var is None:
            return {
                "converged": False,
                "error": "Could not determine grouping variable from formula or arguments"
            }
        
        if group_var not in df.columns:
            return {
                "converged": False,
                "error": f"Grouping variable '{group_var}' not found in DataFrame columns: {list(df.columns)}"
            }
        
        fixed_formula = re.sub(r'\s*\+\s*\(1\|[^)]+\)', '', formula).strip()
        if fixed_formula.startswith('+'):
            fixed_formula = fixed_formula[1:].strip()
        
        logger.info(f"Fitting model with fixed formula: {fixed_formula}, groups: {group_var}")
        
        model = smf.mixedlm(fixed_formula, df, groups=df[group_var])
        result = model.fit()
        
        converged = result.converged
        
        response = {
            "converged": bool(converged),
            "params": {},
            "fixed_effects": {},
            "random_effects": {}
        }
        
        if converged:
            fe = result.fe
            response["fixed_effects"] = {str(k): float(v) for k, v in fe.items()}
            response["params"]["fixed"] = {str(k): float(v) for k, v in fe.items()}
            
            re_cov = result.cov_re
            if re_cov is not None:
                response["random_effects"] = {
                    str(k): float(v) for k, v in re_cov.items()
                }
                response["params"]["random_covariance"] = {str(k): float(v) for k, v in re_cov.items()}
            
            try:
                re_values = result.random_effects
                response["random_effects"]["n_groups"] = len(re_values)
            except Exception as e:
                logger.warning(f"Could not extract random effects values: {e}")
        
        logger.info(f"LMM analysis completed. Converged: {converged}")
        return response
    
    except Exception as e:
        logger.error(f"Error during LMM fitting: {str(e)}", exc_info=True)
        return {
            "converged": False,
            "error": str(e)
        }

def prepare_lmm_data(
    df: pd.DataFrame,
    required_cols: list
) -> pd.DataFrame:
    """
    Prepare data for LMM analysis by ensuring required columns exist and are numeric.
    
    Args:
        df (pd.DataFrame): Input data.
        required_cols (list): List of column names that must be present.
    
    Returns:
        pd.DataFrame: Cleaned data ready for analysis.
    
    Raises:
        ValueError: If required columns are missing.
    """
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    for col in required_cols:
        if col in df.columns and not pd.api.types.is_numeric_dtype(df[col]):
            df[col] = pd.to_numeric(df[col], errors='raise')
    
    return df.dropna(subset=required_cols)

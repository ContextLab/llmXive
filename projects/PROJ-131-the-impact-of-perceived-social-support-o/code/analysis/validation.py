"""
Validation module for the synthetic cohort.
Implements balance checks, variance checks, and multicollinearity diagnostics.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np
import statsmodels.api as sm

logger = logging.getLogger(__name__)

# Thresholds
SMD_THRESHOLD = 0.1
HARASSMENT_SD_THRESHOLD = 0.5
MIN_N_FOR_HARASSMENT = 30
VIF_THRESHOLD = 5.0

def calculate_smd(
    df: pd.DataFrame,
    treatment_col: str = 'dataset_source',
    covariates: List[str] = None
) -> Dict[str, float]:
    """
    Calculate Standardized Mean Differences (SMD) for covariates.
    
    Args:
        df: DataFrame with treatment assignment and covariates
        treatment_col: Column indicating dataset source (0/1)
        covariates: List of covariate column names
        
    Returns:
        Dictionary mapping covariate names to SMD values
    """
    if covariates is None:
        covariates = ['age', 'gender', 'education', 'income', 'social_support', 'harassment_severity']
    
    # Filter to valid columns
    valid_covariates = [c for c in covariates if c in df.columns and treatment_col in df.columns]
    
    smd_results = {}
    
    for col in valid_covariates:
        if df[col].dtype not in [np.float64, np.int64]:
            # Convert categorical to numeric if necessary
            try:
                df_col = pd.Categorical(df[col]).codes
            except:
                logger.warning(f"Skipping non-numeric covariate: {col}")
                continue
        else:
            df_col = df[col]
        
        treated = df_col[df[treatment_col] == 1]
        control = df_col[df[treatment_col] == 0]
        
        if len(treated) == 0 or len(control) == 0:
            smd_results[col] = np.nan
            continue
        
        mean_t = treated.mean()
        mean_c = control.mean()
        std_t = treated.std()
        std_c = control.std()
        
        # Pooled standard deviation
        pooled_std = np.sqrt((std_t**2 + std_c**2) / 2)
        
        if pooled_std == 0:
            smd_results[col] = 0.0
        else:
            smd_results[col] = abs(mean_t - mean_c) / pooled_std
    
    return smd_results

def check_balance(smd_results: Dict[str, float]) -> Tuple[bool, Dict[str, bool]]:
    """
    Check if all covariates meet the SMD threshold.
    
    Args:
        smd_results: Dictionary of SMD values
        
    Returns:
        Tuple of (overall_pass, individual_results)
    """
    individual_results = {}
    all_pass = True
    
    for col, val in smd_results.items():
        if np.isnan(val):
            individual_results[col] = False
            all_pass = False
        elif val <= SMD_THRESHOLD:
            individual_results[col] = True
        else:
            individual_results[col] = False
            all_pass = False
    
    return all_pass, individual_results

def check_harassment_variance(df: pd.DataFrame, var_col: str = 'harassment_exposure') -> Tuple[bool, Dict[str, Any]]:
    """
    Check variance of harassment exposure.
    
    Args:
        df: DataFrame
        var_col: Column name for harassment exposure
        
    Returns:
        Tuple of (pass_check, details)
    """
    if var_col not in df.columns:
        return False, {'error': f"Column {var_col} not found"}
    
    vals = df[var_col].dropna()
    n = len(vals)
    std = vals.std()
    
    details = {
        'n': n,
        'std': std,
        'min': vals.min() if n > 0 else 0,
        'max': vals.max() if n > 0 else 0
    }
    
    passed = (n >= MIN_N_FOR_HARASSMENT) and (std > HARASSMENT_SD_THRESHOLD)
    
    if not passed:
        reason = []
        if n < MIN_N_FOR_HARASSMENT:
            reason.append(f"N={n} < {MIN_N_FOR_HARASSMENT}")
        if std <= HARASSMENT_SD_THRESHOLD:
            reason.append(f"SD={std:.4f} <= {HARASSMENT_SD_THRESHOLD}")
        details['reason'] = "; ".join(reason)
    
    return passed, details

def check_vif(df: pd.DataFrame, formula_vars: List[str] = None) -> Tuple[bool, Dict[str, float]]:
    """
    Check Variance Inflation Factors (VIF) for multicollinearity.
    
    Args:
        df: DataFrame
        formula_vars: List of variables to check
        
    Returns:
        Tuple of (all_pass, vif_dict)
    """
    if formula_vars is None:
        formula_vars = ['social_support', 'harassment_exposure', 'social_support:harassment_exposure', 
                        'age', 'gender', 'education', 'income']
    
    # Ensure interaction term exists if requested
    if 'social_support:harassment_exposure' in formula_vars:
        if 'social_support:harassment_exposure' not in df.columns:
            df = df.copy()
            df['social_support:harassment_exposure'] = df['social_support'] * df['harassment_exposure']
    
    # Prepare data
    cols_to_use = [v for v in formula_vars if v in df.columns]
    if len(cols_to_use) < 2:
        return True, {}
    
    clean_df = df[cols_to_use].dropna()
    X = sm.add_constant(clean_df)
    
    vif_dict = {}
    max_vif = 0
    
    for i, col in enumerate(X.columns):
        if col == 'const':
            continue
        
        try:
            vif = sm.stats.variance_inflation_factor(X.values, i)
            vif_dict[col] = vif
            max_vif = max(max_vif, vif)
        except Exception:
            vif_dict[col] = np.nan
    
    passed = all(v < VIF_THRESHOLD for v in vif_dict.values() if not np.isnan(v))
    
    return passed, vif_dict

def validate_synthetic_cohort(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Run all validation checks on the synthetic cohort.
    
    Args:
        df: The synthetic cohort DataFrame
        
    Returns:
        Dictionary with validation results
    """
    logger.info("Starting validation of synthetic cohort")
    
    results = {
        'smd_check': {},
        'harassment_check': {},
        'vif_check': {},
        'overall_valid': True,
        'warnings': []
    }
    
    # SMD Check
    smd_vals = calculate_smd(df)
    smd_pass, smd_details = check_balance(smd_vals)
    results['smd_check'] = {
        'passed': smd_pass,
        'threshold': SMD_THRESHOLD,
        'values': smd_vals
    }
    if not smd_pass:
        results['overall_valid'] = False
        results['warnings'].append(f"SMD check failed: {smd_details}")
    
    # Harassment Variance Check
    harm_pass, harm_details = check_harassment_variance(df)
    results['harassment_check'] = harm_details
    if not harm_pass:
        results['overall_valid'] = False
        results['warnings'].append(f"Harassment variance check failed: {harm_details.get('reason', 'unknown')}")
    
    # VIF Check
    vif_pass, vif_vals = check_vif(df)
    results['vif_check'] = {
        'passed': vif_pass,
        'threshold': VIF_THRESHOLD,
        'values': vif_vals
    }
    if not vif_pass:
        results['overall_valid'] = False
        results['warnings'].append(f"VIF check failed: max VIF > {VIF_THRESHOLD}")
    
    logger.info(f"Validation complete. Overall valid: {results['overall_valid']}")
    return results

def main():
    """Main entry point for validation."""
    logging.basicConfig(level=logging.INFO)
    
    # Load data
    try:
        df = pd.read_csv("data/results/synthetic_cohort.csv")
    except FileNotFoundError:
        logger.error("Synthetic cohort not found. Run cohort construction first.")
        return None
    
    # Validate
    results = validate_synthetic_cohort(df)
    
    # Log results
    if results['overall_valid']:
        logger.info("All validation checks passed.")
    else:
        logger.warning("Validation failed with warnings: " + "; ".join(results['warnings']))
    
    return results

if __name__ == "__main__":
    main()

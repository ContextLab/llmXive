import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple, Any
from src.analysis.psm import iterative_matching
from src.analysis.balance import (
    calculate_smd,
    run_placebo_test,
    validate_placebo_results,
    check_placebo_significance,
    generate_placebo_report
)
from src.data.preprocess import PowerError
from src.analysis.causal import run_ols, run_did, DataUnavailableError
from src.utils.logging import get_logger

logger = get_logger(__name__)

class PlaceboGateError(Exception):
    """Raised when the placebo test fails, blocking causal estimation."""
    pass

class BalanceFailureError(Exception):
    """Raised when PSM fails to achieve balance and DiD fallback is not possible or fails."""
    pass

def run_placebo_gate(matched_df: pd.DataFrame, alpha: float = 0.05) -> Tuple[bool, Dict[str, Any]]:
    """
    Execute the placebo test on matched data to ensure no pre-treatment differences exist.
    
    Args:
        matched_df: DataFrame containing matched pairs with treatment and pre-treatment outcome.
        alpha: Significance level for the test.
        
    Returns:
        Tuple of (passed: bool, report: dict)
        
    Raises:
        ValueError: If required columns are missing.
    """
    logger.info("Running placebo gate check...")
    
    required_cols = ['treatment', 'pre_treatment_outcome']
    missing = [c for c in required_cols if c not in matched_df.columns]
    if missing:
        raise ValueError(f"Placebo test requires columns: {missing}")
        
    p_value = run_placebo_test(matched_df, outcome_col='pre_treatment_outcome', treatment_col='treatment')
    passed = p_value > alpha
    
    report = {
        'p_value': p_value,
        'threshold': alpha,
        'passed': passed,
        'methodology': 'Placebo test on pre-treatment outcome'
    }
    
    if not passed:
        logger.warning(f"Placebo test failed (p={p_value:.4f} <= {alpha}). Groups differ pre-treatment.")
    else:
        logger.info(f"Placebo test passed (p={p_value:.4f} > {alpha}).")
        
    return passed, report

def run_full_pipeline(
    df: pd.DataFrame,
    caliper: float = 0.05,
    placebo_alpha: float = 0.05,
    max_attempts: int = 5
) -> Dict[str, Any]:
    """
    Execute the full causal inference pipeline with control flow logic.
    
    This function:
    1. Runs iterative PSM to achieve balance.
    2. Checks the placebo test.
    3. If placebo passes, runs OLS.
    4. If placebo fails but balance was achieved, triggers DiD fallback if data available.
    5. Handles missing longitudinal data gracefully with specific error paths.
    
    Args:
        df: Preprocessed dataframe with treatment, outcome, and covariates.
        caliper: Initial caliper width for matching.
        placebo_alpha: Significance threshold for placebo test.
        max_attempts: Maximum iterations for balance adjustment.
        
    Returns:
        Dictionary containing results, methodology, and status flags.
    """
    logger.info("Starting full causal inference pipeline...")
    
    result = {
        'status': 'success',
        'methodology': None,
        'att_estimate': None,
        'p_value': None,
        'confidence_interval': None,
        'balance_status': None,
        'placebo_report': None,
        'error': None,
        'fallback_triggered': False
    }
    
    # Step 1: Propensity Score Matching with Balance Adjustment
    try:
        logger.info(f"Running iterative matching with initial caliper={caliper}")
        matched_df, balance_status = iterative_matching(
            df, 
            caliper=caliper, 
            max_attempts=max_attempts
        )
        result['balance_status'] = balance_status
        
        if matched_df is None or len(matched_df) == 0:
            raise BalanceFailureError("PSM failed to produce any matched pairs.")
            
    except Exception as e:
        logger.error(f"PSM failed: {e}")
        result['status'] = 'failure'
        result['error'] = f"PSM Error: {str(e)}"
        return result
    
    # Step 2: Placebo Test
    try:
        placebo_passed, placebo_report = run_placebo_gate(matched_df, alpha=placebo_alpha)
        result['placebo_report'] = placebo_report
        
        if not placebo_passed:
            logger.warning("Placebo test failed. Triggering DiD fallback logic.")
            result['fallback_triggered'] = True
    except ValueError as e:
        logger.error(f"Placebo test configuration error: {e}")
        result['status'] = 'failure'
        result['error'] = f"Placebo Error: {str(e)}"
        return result
    
    # Step 3: Causal Estimation (Control Flow Logic)
    try:
        if result['fallback_triggered']:
            # Fallback to DiD
            logger.info("Attempting DiD fallback due to placebo failure...")
            try:
                did_result = run_did(matched_df)
                result['methodology'] = 'Difference-in-Differences (Fallback)'
                result['att_estimate'] = did_result['estimate']
                result['p_value'] = did_result['p_value']
                result['confidence_interval'] = did_result['ci']
                logger.info("DiD fallback successful.")
            except DataUnavailableError as e:
                # Specific error path for missing longitudinal data
                logger.error(f"DiD fallback failed: {e}")
                result['status'] = 'failure'
                result['error'] = f"DataUnavailableError: {str(e)}"
                return result
            except Exception as e:
                logger.error(f"DiD execution failed: {e}")
                result['status'] = 'failure'
                result['error'] = f"DiD Error: {str(e)}"
                return result
        else:
            # Proceed to OLS
            logger.info("Placebo passed. Running OLS estimation.")
            ols_result = run_ols(matched_df)
            result['methodology'] = 'Propensity Score Matching with OLS'
            result['att_estimate'] = ols_result['estimate']
            result['p_value'] = ols_result['p_value']
            result['confidence_interval'] = ols_result['ci']
            logger.info("OLS estimation successful.")
            
    except Exception as e:
        logger.error(f"Causal estimation failed: {e}")
        result['status'] = 'failure'
        result['error'] = f"Causal Estimation Error: {str(e)}"
        return result
        
    logger.info("Pipeline completed successfully.")
    return result
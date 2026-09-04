import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple, Any
from src.analysis.psm import iterative_matching
from src.analysis.balance import run_placebo_test, check_placebo_significance, generate_placebo_report
from src.data.preprocess import PowerError
from src.analysis.causal import run_ols, run_did, DataUnavailableError, estimate_causal_effect
from src.utils.logging import get_logger

logger = get_logger(__name__)

class PlaceboGateError(Exception):
    """Raised when the placebo test indicates significant pre-treatment differences."""
    pass

class BalanceFailureError(Exception):
    """Raised when propensity score matching fails to achieve balance."""
    pass

def run_placebo_gate(matched_data: pd.DataFrame, alpha: float = 0.05) -> Tuple[bool, Dict[str, Any]]:
    """
    Execute the placebo test and gate the causal estimation flow.

    Args:
        matched_data: DataFrame containing matched treatment and control pairs.
        alpha: Significance level for the placebo test.

    Returns:
        Tuple of (gate_passed: bool, report: dict)

    Raises:
        PlaceboGateError: If the placebo test is significant (p < alpha).
    """
    logger.info("Running placebo test gate...")
    
    try:
        placebo_result = run_placebo_test(matched_data)
        passed = check_placebo_significance(placebo_result, alpha=alpha)
        report = generate_placebo_report(placebo_result)
        
        if not passed:
            logger.error(f"Placebo test failed: p-value {placebo_result['p_value']:.4f} < {alpha}")
            raise PlaceboGateError(
                f"Placebo test failed (p={placebo_result['p_value']:.4f}). "
                "Pre-treatment outcomes differ significantly between groups. "
                "Causal estimation halted."
            )
        
        logger.info(f"Placebo test passed (p={placebo_result['p_value']:.4f}). Proceeding to causal estimation.")
        return True, report
        
    except Exception as e:
        logger.error(f"Placebo gate execution failed: {str(e)}")
        raise

def run_full_pipeline(
    matched_data: pd.DataFrame,
    balance_status: bool,
    caliper: float = 0.05,
    alpha: float = 0.05,
    placebo_enabled: bool = True
) -> Dict[str, Any]:
    """
    Execute the full causal inference pipeline with control flow logic.
    
    This function implements the decision logic for T053:
    1. Checks `balance_status` to determine if PSM succeeded.
    2. If balance failed, attempts DiD fallback (T054).
    3. If balance succeeded, proceeds to OLS (T028).
    4. Enforces placebo gate if enabled.
    5. Handles missing data errors for DiD explicitly.

    Args:
        matched_data: DataFrame with matched pairs and outcome variables.
        balance_status: Boolean flag from Phase 4 indicating if PSM achieved balance (True) or failed (False).
        caliper: Caliper value used for matching (passed through for sensitivity context).
        alpha: Significance level for hypothesis tests.
        placebo_enabled: Whether to run the placebo gate check.

    Returns:
        Dictionary containing:
            - 'methodology': 'OLS' or 'DiD'
            - 'balance_status': The input balance status
            - 'result': The causal estimate object from run_ols or run_did
            - 'error': Error message if pipeline failed
            - 'placebo_report': Output from placebo test if run
    """
    logger.info("Starting full pipeline execution with control flow logic...")
    logger.info(f"Balance status received: {balance_status}")

    result = {
        'methodology': None,
        'balance_status': balance_status,
        'result': None,
        'error': None,
        'placebo_report': None
    }

    # Step 1: Handle Placebo Gate if enabled and balance was successful
    if balance_status and placebo_enabled:
        try:
            passed, placebo_report = run_placebo_gate(matched_data, alpha=alpha)
            result['placebo_report'] = placebo_report
        except PlaceboGateError as e:
            result['error'] = str(e)
            result['methodology'] = 'Halted (Placebo Failure)'
            logger.critical(f"Pipeline halted due to placebo gate: {e}")
            return result

    # Step 2: Decision Logic based on Balance Status
    if not balance_status:
        logger.warning("PSM Balance failed. Attempting DiD fallback (T054)...")
        try:
            # Attempt DiD estimation
            # This will raise DataUnavailableError if longitudinal columns are missing
            did_result = run_did(matched_data)
            result['methodology'] = 'DiD (Fallback)'
            result['result'] = did_result
            logger.info("DiD fallback successful.")
        except DataUnavailableError as e:
            # Explicit error path for missing longitudinal data
            logger.critical(f"DiD fallback failed due to missing data: {e}")
            result['methodology'] = 'Failed'
            result['error'] = (
                f"PSM balance failed AND DiD fallback unavailable: {str(e)}. "
                "Cannot estimate causal effect. Longitudinal data required for DiD but missing."
            )
            raise BalanceFailureError(result['error'])
        except Exception as e:
            logger.error(f"DiD estimation failed unexpectedly: {e}")
            result['methodology'] = 'Failed'
            result['error'] = f"DiD fallback failed: {str(e)}"
    else:
        logger.info("PSM Balance successful. Proceeding to OLS estimation (T028)...")
        try:
            ols_result = run_ols(matched_data)
            result['methodology'] = 'OLS'
            result['result'] = ols_result
            logger.info("OLS estimation successful.")
        except Exception as e:
            logger.error(f"OLS estimation failed: {e}")
            result['methodology'] = 'Failed'
            result['error'] = f"OLS estimation failed: {str(e)}"

    return result
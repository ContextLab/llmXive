"""
Utilities for chi-squared tests with fallback logic.
Implements T013: Check expected cell counts < 5 and route to fallback.
"""
import numpy as np
from scipy import stats
from typing import Tuple, Dict, Any, Optional
import warnings

from code.simulation.logging_config import get_logger

logger = get_logger("chi_squared_utils")

def calculate_expected_counts(contingency: np.ndarray) -> np.ndarray:
    """
    Calculate expected counts for a contingency table.
    """
    row_totals = contingency.sum(axis=1, keepdims=True)
    col_totals = contingency.sum(axis=0, keepdims=True)
    total = contingency.sum()
    expected = (row_totals * col_totals) / total
    return expected

def check_low_expected_counts(contingency: np.ndarray, threshold: float = 5.0) -> bool:
    """
    Check if any expected cell count is below the threshold.
    """
    expected = calculate_expected_counts(contingency)
    return np.any(expected < threshold)

def run_chi_squared_with_fallback(contingency: np.ndarray, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Run chi-squared test with fallback to Fisher's exact test for 2x2 tables
    or Yates' correction if expected counts are low.
    """
    try:
        # Check if 2x2 table
        if contingency.shape == (2, 2):
            # Check expected counts
            if check_low_expected_counts(contingency):
                # Use Fisher's exact test
                try:
                    oddsratio, p_value = stats.fisher_exact(contingency)
                    return {
                        "method": "fisher_exact",
                        "p_value": p_value,
                        "statistic": float(oddsratio)
                    }
                except Exception as e:
                    logger.log("fisher_exact_failed", error=str(e))
                    # Fall back to chi-squared with Yates' correction
            
            # Use chi-squared with Yates' correction for 2x2
            stat, p_value = stats.chi2_contingency(contingency, correction=True)
            return {
                "method": "chi2_yates",
                "p_value": p_value,
                "statistic": float(stat)
            }
        else:
            # For larger tables, use chi-squared
            stat, p_value = stats.chi2_contingency(contingency, correction=False)
            return {
                "method": "chi2_standard",
                "p_value": p_value,
                "statistic": float(stat)
            }
    except Exception as e:
        logger.log("chi_squared_error", error=str(e))
        return {
            "method": "error",
            "p_value": np.nan,
            "statistic": np.nan,
            "error": str(e)
        }

def main():
    """Main entry point for testing."""
    logger.log("chi_squared_utils_main")

if __name__ == "__main__":
    main()

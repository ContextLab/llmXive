"""
Task T025: Implement Shapiro-Wilk test for distribution normality check on residuals.

This module loads the Linear Mixed-Effects Regression (LMER) results, extracts the
residuals, and performs the Shapiro-Wilk test to check the normality assumption.

Output: Appends 'shapiro_p_value' to 'data/analysis_results.json'.
"""
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np
from scipy import stats

# Add parent to path for imports if running as script
if str(Path(__file__).resolve().parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.logging_config import get_logger

logger = get_logger(__name__)

def load_analysis_results() -> Dict[str, Any]:
    """
    Load the existing analysis results from JSON.
    """
    results_path = Path("data/analysis_results.json")
    if not results_path.exists():
        logger.error(f"Analysis results file not found at {results_path}")
        raise FileNotFoundError(f"Analysis results file not found at {results_path}")
    
    with open(results_path, 'r') as f:
        return json.load(f)

def save_analysis_results(results: Dict[str, Any]) -> None:
    """
    Save the updated analysis results to JSON.
    """
    results_path = Path("data/analysis_results.json")
    results_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved updated analysis results to {results_path}")

def extract_residuals_from_lmer(lmer_results: Dict[str, Any]) -> Optional[np.ndarray]:
    """
    Extract residuals from the LMER results.
    
    The LMER results are expected to contain a 'residuals' key with the
    array of residuals. If not present, we may need to reconstruct them
    or return None if the data is missing.
    """
    if 'residuals' in lmer_results:
        residuals = np.array(lmer_results['residuals'])
        logger.info(f"Extracted {len(residuals)} residuals from LMER results.")
        return residuals
    else:
        logger.warning("No 'residuals' key found in LMER results. "
                     "Cannot perform Shapiro-Wilk test without residuals.")
        return None

def perform_shapiro_wilk_test(residuals: np.ndarray) -> float:
    """
    Perform the Shapiro-Wilk test for normality on the residuals.
    
    Args:
        residuals: Array of residuals from the regression model.
        
    Returns:
        The p-value from the Shapiro-Wilk test.
    """
    if len(residuals) < 3:
        logger.warning("Not enough data points (n < 3) to perform Shapiro-Wilk test.")
        return np.nan
    
    # Shapiro-Wilk test is valid for sample sizes up to 5000 in older scipy versions.
    # For larger samples, it might raise a ValueError. We handle this gracefully.
    try:
        stat, p_value = stats.shapiro(residuals)
        logger.info(f"Shapiro-Wilk Test: Statistic={stat:.4f}, P-value={p_value:.4f}")
        return p_value
    except ValueError as e:
        # If sample size is too large for scipy.stats.shapiro, we can fall back to
        # the Anderson-Darling test or just log the issue. However, the task
        # specifically asks for Shapiro-Wilk. We'll log the error and return NaN.
        logger.error(f"Shapiro-Wilk test failed due to sample size constraints: {e}")
        return np.nan

def run_shapiro_test() -> float:
    """
    Main function to run the Shapiro-Wilk test on LMER residuals.
    
    Returns:
        The p-value from the test.
    """
    logger.info("Starting Shapiro-Wilk test for normality check on residuals.")
    
    # Load existing results
    results = load_analysis_results()
    
    # Extract LMER results
    if 'lmer' not in results:
        logger.error("No LMER results found in analysis_results.json. "
                    "Cannot perform Shapiro-Wilk test.")
        raise ValueError("LMER results not found in analysis_results.json")
    
    lmer_results = results['lmer']
    
    # Extract residuals
    residuals = extract_residuals_from_lmer(lmer_results)
    
    if residuals is None:
        logger.warning("Skipping Shapiro-Wilk test due to missing residuals.")
        results['shapiro_p_value'] = None
    else:
        p_value = perform_shapiro_wilk_test(residuals)
        results['shapiro_p_value'] = p_value
        
        if p_value is not None:
            alpha = 0.05
            if p_value < alpha:
                logger.warning(f"Residuals are NOT normally distributed (p={p_value:.4f} < {alpha}). "
                             "Assumption of normality violated.")
            else:
                logger.info(f"Residuals appear to be normally distributed (p={p_value:.4f} >= {alpha}).")
    
    # Save updated results
    save_analysis_results(results)
    
    return results['shapiro_p_value']

def main():
    """Entry point for the script."""
    try:
        p_value = run_shapiro_test()
        if p_value is not None:
            print(f"Shapiro-Wilk P-value: {p_value:.6f}")
        else:
            print("Shapiro-Wilk test could not be performed (missing residuals).")
    except Exception as e:
        logger.error(f"Error during Shapiro-Wilk test execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

import logging
import sys
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import pandas as pd
from statsmodels.stats.sandwich_covariance import cov_hc0

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def _calculate_taylor_variance(series: pd.Series, weights: pd.Series) -> float:
    """
    Calculates the Taylor series linearization variance for a single variable.
    
    Parameters:
        series: The variable of interest (must be non-missing).
        weights: The survey weights corresponding to the series.
        
    Returns:
        float: The estimated variance.
    """
    # Filter out any remaining NaNs just in case, though caller should handle this
    mask = series.notna() & weights.notna()
    y = series[mask].values
    w = weights[mask].values

    if len(y) == 0:
        raise ValueError("No valid data points after masking.")
    
    # Weighted mean
    w_sum = np.sum(w)
    mean = np.sum(w * y) / w_sum

    # Weighted variance calculation (Taylor linearization approximation)
    # Variance of weighted mean: (1 / (sum(w))^2) * sum(w_i^2 * (y_i - mean)^2)
    # This is the HC0 sandwich estimator form for the mean
    residuals = y - mean
    weighted_sq_residuals = (w ** 2) * (residuals ** 2)
    variance_est = np.sum(weighted_sq_residuals) / (w_sum ** 2)
    
    return variance_est

def _check_psu_sizes(df: pd.DataFrame, psu_col: str) -> Tuple[bool, List[int]]:
    """
    Checks the size of clusters defined by the PSU column.
    
    Returns:
        Tuple[has_singletons, list_of_singleton_psus]
        has_singletons: True if any PSU has size 1.
        list_of_singleton_psus: List of PSU IDs that have size 1.
    """
    if psu_col not in df.columns:
        return False, []
    
    psu_counts = df.groupby(psu_col).size()
    singletons = psu_counts[psu_counts == 1].index.tolist()
    has_singletons = len(singletons) > 0
    
    return has_singletons, singletons

def estimate_taylor_variance(
    df: pd.DataFrame,
    variable: str,
    weight_col: str = 'weight',
    psu_col: str = 'psu',
    strata_col: str = 'strata'
) -> Dict[str, Any]:
    """
    Estimates the design-based variance for a single variable using Taylor series linearization.
    
    This implementation includes the T009b edge case handling:
    - If PSU column is missing, it aborts (as per T009).
    - If PSU column exists but contains clusters of size 1 (singletons),
      it issues a warning and flags the variance as 'potentially unstable'
      but continues calculation (T009b requirement).
    
    Parameters:
        df: The DataFrame containing the data.
        variable: The name of the variable to estimate variance for.
        weight_col: Name of the weight column.
        psu_col: Name of the PSU (cluster) column.
        strata_col: Name of the strata column (not strictly used in HC0 mean variance
                    but required for full design validation in T009 context).
                    
    Returns:
        Dict containing:
            - 'mean': The weighted mean.
            - 'variance': The estimated variance.
            - 'status': 'success', 'warning', or 'error'.
            - 'message': Details about the calculation (e.g., singleton warnings).
            - 'is_unstable': Boolean flag for T009b (True if singletons detected).
    """
    result = {
        'mean': None,
        'variance': None,
        'status': 'success',
        'message': '',
        'is_unstable': False
    }

    # T009 Check: Ensure design columns exist
    required_cols = [variable, weight_col, psu_col, strata_col]
    missing_cols = [c for c in required_cols if c not in df.columns]
    
    if missing_cols:
        logger.error(f"Missing required design columns: {missing_cols}. Aborting analysis.")
        result['status'] = 'error'
        result['message'] = f"Missing design columns: {missing_cols}. Aborting as per T009."
        return result

    # T009b Check: Detect small clusters (PSU size = 1)
    has_singletons, singleton_psus = _check_psu_sizes(df, psu_col)
    
    if has_singletons:
        msg = (f"Detected {len(singleton_psus)} PSU clusters with size 1. "
               f"Variance estimate may be unstable. Proceeding with warning.")
        logger.warning(msg)
        result['is_unstable'] = True
        result['status'] = 'warning'
        result['message'] = msg

    # Filter for complete cases for the specific variable
    mask = df[variable].notna() & df[weight_col].notna()
    subset = df.loc[mask, [variable, weight_col]]
    
    if len(subset) == 0:
        result['status'] = 'error'
        result['message'] = "No valid data points found for the variable after masking."
        return result

    try:
        # Calculate weighted mean
        w_sum = subset[weight_col].sum()
        weighted_mean = (subset[variable] * subset[weight_col]).sum() / w_sum
        
        # Calculate Taylor variance
        variance = _calculate_taylor_variance(subset[variable], subset[weight_col])
        
        result['mean'] = float(weighted_mean)
        result['variance'] = float(variance)
        
    except Exception as e:
        result['status'] = 'error'
        result['message'] = f"Calculation failed: {str(e)}"
        logger.error(f"Variance calculation error: {e}")

    return result

def estimate_variance_for_multiple_variables(
    df: pd.DataFrame,
    variables: List[str],
    weight_col: str = 'weight',
    psu_col: str = 'psu',
    strata_col: str = 'strata'
) -> Dict[str, Dict[str, Any]]:
    """
    Estimates variance for multiple variables and aggregates results.
    
    Returns a dictionary mapping variable names to their individual result dicts.
    """
    results = {}
    for var in variables:
        logger.info(f"Estimating variance for {var}...")
        results[var] = estimate_taylor_variance(
            df, var, weight_col, psu_col, strata_col
        )
    return results

def main():
    """
    Main entry point for the variance estimator script.
    Reads data from data/raw/gss_2018_subset.csv and outputs results to data/processed/variance_results.json.
    """
    import json
    from pathlib import Path

    # Define paths
    input_path = Path("data/raw/gss_2018_subset.csv")
    output_path = Path("data/processed/variance_results.json")

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}. Please run data ingestion first.")
        sys.exit(1)

    # Load data
    try:
        df = pd.read_csv(input_path)
        logger.info(f"Loaded data with shape {df.shape}")
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        sys.exit(1)

    # Define variables of interest (example: age, hours)
    # In a real pipeline, these might be passed via config or derived from missingness checks
    variables_of_interest = ['age', 'hours']
    
    # Filter to variables present in dataframe
    available_vars = [v for v in variables_of_interest if v in df.columns]
    if not available_vars:
        logger.warning("No variables of interest found in the dataset.")
        sys.exit(0)

    # Run estimation
    results = estimate_variance_for_multiple_variables(
        df, 
        available_vars,
        weight_col='weight',
        psu_col='psu',
        strata_col='strata'
    )

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save results
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Results saved to {output_path}")

    # Print summary
    for var, res in results.items():
        print(f"{var}: Mean={res['mean']:.2f}, Var={res['variance']:.4f}, Status={res['status']}, Unstable={res['is_unstable']}")

if __name__ == "__main__":
    main()
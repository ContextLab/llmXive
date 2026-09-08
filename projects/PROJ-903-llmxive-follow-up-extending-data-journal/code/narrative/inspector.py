import os
import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set

import numpy as np
import pandas as pd
from scipy import stats

from config import get_config
from data.loader import LowPowerError

logger = logging.getLogger(__name__)


def compute_partial_correlation(
    df: pd.DataFrame,
    var_x: str,
    var_y: str,
    control_vars: List[str]
) -> Tuple[float, float]:
    """
    Compute partial correlation between var_x and var_y controlling for control_vars.
    
    Returns:
        Tuple of (partial_r, p_value)
    """
    if not control_vars:
        # If no control variables, return standard Pearson correlation
        r, p = stats.pearsonr(df[var_x], df[var_y])
        return r, p

    # Check for sufficient data
    if len(df) < 30:
        raise LowPowerError(f"Insufficient sample size ({len(df)}) for partial correlation")

    # Residualize var_x against control variables
    X = df[control_vars].values
    y_x = df[var_x].values
    
    # Add intercept
    X_with_intercept = np.column_stack([np.ones(len(X)), X])
    
    # Fit linear model for var_x ~ control_vars
    try:
        coeffs_x = np.linalg.lstsq(X_with_intercept, y_x, rcond=None)[0]
        residuals_x = y_x - X_with_intercept @ coeffs_x
    except np.linalg.LinAlgError:
        logger.warning("Singular matrix in partial correlation for var_x. Using direct correlation.")
        r, p = stats.pearsonr(df[var_x], df[var_y])
        return r, p

    # Residualize var_y against control variables
    y_y = df[var_y].values
    try:
        coeffs_y = np.linalg.lstsq(X_with_intercept, y_y, rcond=None)[0]
        residuals_y = y_y - X_with_intercept @ coeffs_y
    except np.linalg.LinAlgError:
        logger.warning("Singular matrix in partial correlation for var_y. Using direct correlation.")
        r, p = stats.pearsonr(df[var_x], df[var_y])
        return r, p

    # Compute correlation of residuals
    partial_r, partial_p = stats.pearsonr(residuals_x, residuals_y)
    
    return partial_r, partial_p


def bootstrap_stability_analysis(
    df: pd.DataFrame,
    var_x: str,
    var_y: str,
    control_vars: List[str],
    n_iterations: int = 100,
    sample_fraction: float = 0.8,
    p_threshold: float = 0.05,
    r_threshold: float = 0.15
) -> Dict[str, Any]:
    """
    Perform bootstrap stability analysis for partial correlation.
    
    Args:
        df: Input DataFrame
        var_x: Primary variable X
        var_y: Primary variable Y
        control_vars: Variables to control for
        n_iterations: Number of bootstrap iterations
        sample_fraction: Fraction of data to sample per iteration
        p_threshold: P-value threshold for significance
        r_threshold: Absolute partial r threshold for validity
        
    Returns:
        Dictionary containing stability metrics and results
    """
    if len(df) < 30:
        raise LowPowerError(f"Insufficient sample size ({len(df)}) for bootstrap analysis")

    logger.info(f"Starting bootstrap stability analysis: {n_iterations} iterations")
    
    valid_count = 0
    partial_rs = []
    p_values = []
    
    n_samples = int(len(df) * sample_fraction)
    
    for i in range(n_iterations):
        # Resample with replacement
        sample_df = df.sample(n=n_samples, replace=True, random_state=i)
        
        try:
            partial_r, p_val = compute_partial_correlation(
                sample_df, var_x, var_y, control_vars
            )
            
            partial_rs.append(partial_r)
            p_values.append(p_val)
            
            # Check if this resample passes FR-003 thresholds
            if p_val < p_threshold and abs(partial_r) > r_threshold:
                valid_count += 1
                
        except (LowPowerError, np.linalg.LinAlgError, ValueError) as e:
            logger.debug(f"Bootstrap iteration {i} failed: {e}")
            continue

    stability_score = valid_count / n_iterations if n_iterations > 0 else 0.0
    
    # Compute mean and std of partial correlations
    mean_partial_r = np.mean(partial_rs) if partial_rs else 0.0
    std_partial_r = np.std(partial_rs) if partial_rs else 0.0
    
    return {
        "stability_score": round(stability_score, 4),
        "mean_partial_r": round(mean_partial_r, 4),
        "std_partial_r": round(std_partial_r, 4),
        "n_iterations": n_iterations,
        "valid_count": valid_count,
        "total_attempts": n_iterations
    }


def determine_validity_status(
    stability_score: float,
    original_p: float,
    sample_size: int,
    stability_threshold: float = 0.8,
    p_threshold: float = 0.05
) -> str:
    """
    Determine the validity status based on stability and p-value.
    
    Args:
        stability_score: Bootstrap stability score (0-1)
        original_p: Original p-value
        sample_size: Sample size of the dataset
        stability_threshold: Minimum stability score for "verified"
        p_threshold: P-value threshold for significance
        
    Returns:
        One of: "verified", "low_power", "confounded", "failed"
    """
    if sample_size < 30:
        return "low_power"
    
    if stability_score >= stability_threshold and original_p < p_threshold:
        return "verified"
    
    if stability_score < stability_threshold:
        return "confounded"
    
    return "failed"


def run_inspector_analysis(
    df: pd.DataFrame,
    baseline_narrative: Dict[str, Any],
    candidate_variables: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Run full inspector analysis including partial correlations and stability checks.
    
    Args:
        df: Processed DataFrame
        baseline_narrative: Output from baseline analysis containing primary drivers
        candidate_variables: Optional list of candidate variables to test
        
    Returns:
        List of analysis results with stability scores and validity status
    """
    if candidate_variables is None:
        # Default: use all numeric columns except the primary ones
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        primary_vars = [baseline_narrative.get("var_x"), baseline_narrative.get("var_y")]
        candidate_variables = [c for c in numeric_cols if c not in primary_vars]
    
    results = []
    
    var_y = baseline_narrative.get("var_y")
    if not var_y:
        logger.warning("No target variable found in baseline narrative")
        return results

    for candidate in candidate_variables:
        if candidate == var_y or candidate not in df.columns:
            continue
        
        # Control for top baseline drivers
        control_vars = [baseline_narrative.get("var_x")]
        
        try:
            # Compute partial correlation
            partial_r, p_value = compute_partial_correlation(
                df, candidate, var_y, control_vars
            )
            
            # Perform bootstrap stability analysis
            stability_results = bootstrap_stability_analysis(
                df, candidate, var_y, control_vars
            )
            
            # Determine validity status
            validity_status = determine_validity_status(
                stability_results["stability_score"],
                p_value,
                len(df)
            )
            
            result = {
                "candidate_variable": candidate,
                "target_variable": var_y,
                "control_variables": control_vars,
                "partial_r": round(partial_r, 4),
                "p_value": round(p_value, 4),
                "stability_score": stability_results["stability_score"],
                "mean_partial_r": stability_results["mean_partial_r"],
                "std_partial_r": stability_results["std_partial_r"],
                "validity_status": validity_status,
                "sample_size": len(df)
            }
            
            results.append(result)
            
        except LowPowerError as e:
            logger.warning(f"Low power error for candidate {candidate}: {e}")
            results.append({
                "candidate_variable": candidate,
                "target_variable": var_y,
                "control_variables": control_vars,
                "partial_r": None,
                "p_value": None,
                "stability_score": None,
                "mean_partial_r": None,
                "std_partial_r": None,
                "validity_status": "low_power",
                "sample_size": len(df),
                "error": str(e)
            })
        except Exception as e:
            logger.error(f"Error processing candidate {candidate}: {e}")
            results.append({
                "candidate_variable": candidate,
                "target_variable": var_y,
                "control_variables": control_vars,
                "partial_r": None,
                "p_value": None,
                "stability_score": None,
                "mean_partial_r": None,
                "std_partial_r": None,
                "validity_status": "failed",
                "sample_size": len(df),
                "error": str(e)
            })
    
    return results


def main():
    """
    Main entry point for inspector analysis.
    Reads processed data and baseline narrative, runs analysis, outputs results.
    """
    logging.basicConfig(level=logging.INFO)
    
    config = get_config()
    data_dir = Path(config.data_dir)
    output_dir = Path(config.output_dir)
    
    # Load processed data
    processed_file = data_dir / "processed" / "cleaned_data.csv"
    if not processed_file.exists():
        raise FileNotFoundError(f"Processed data not found: {processed_file}")
    
    df = pd.read_csv(processed_file)
    
    # Load baseline narrative
    baseline_file = output_dir / "baseline_narrative.json"
    if not baseline_file.exists():
        raise FileNotFoundError(f"Baseline narrative not found: {baseline_file}")
    
    with open(baseline_file, 'r') as f:
        baseline_narrative = json.load(f)
    
    logger.info(f"Running inspector analysis on {len(df)} rows")
    
    # Run analysis
    results = run_inspector_analysis(df, baseline_narrative)
    
    # Write results to output
    output_file = output_dir / "inspector_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Inspector analysis complete. Results written to {output_file}")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
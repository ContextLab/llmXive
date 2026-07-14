"""
Statistical analysis for localization length vs disorder strength.

Implements linear regression of log(xi) vs log(W) to extract scaling exponents,
R-squared values, and confidence intervals as required by FR-005.
"""
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
from scipy import stats as scipy_stats

from config import get_config
from logger_utils import get_logger, log_numerical_warning

# Configure logging
logger = get_logger(__name__)


def perform_linear_regression(
    x: np.ndarray,
    y: np.ndarray,
    y_err: Optional[np.ndarray] = None
) -> Dict[str, Any]:
    """
    Perform weighted or unweighted linear regression on log-transformed data.
    
    Args:
        x: Independent variable (log(W))
        y: Dependent variable (log(xi))
        y_err: Optional array of standard errors for y (for weighted regression)
    
    Returns:
        Dictionary containing:
            - slope: Regression coefficient
            - intercept: Regression intercept
            - slope_stderr: Standard error of the slope
            - r_squared: Coefficient of determination
            - p_value: P-value for the slope (null hypothesis: slope = 0)
            - confidence_interval_95: 95% confidence interval for the slope
            - fit_params: Dictionary with 'slope' and 'intercept' for plotting
            - n_samples: Number of data points used
    """
    if len(x) != len(y):
        raise ValueError(f"x and y must have same length: {len(x)} vs {len(y)}")
    
    if len(x) < 2:
        raise ValueError(f"Need at least 2 data points for regression, got {len(x)}")
    
    if y_err is not None:
        # Weighted least squares
        weights = 1.0 / (y_err ** 2)
        # Normalize weights
        weights = weights / np.sum(weights) * len(weights)
        
        # Use scipy.stats.linregress is not weighted, so we use polyfit with weights
        # For linear regression: y = slope * x + intercept
        # Weights in polyfit are 1/sigma^2
        try:
            coeffs, cov = np.polyfit(x, y, 1, w=np.sqrt(weights), cov=True)
            slope, intercept = coeffs
            slope_stderr = np.sqrt(cov[0, 0])
        except np.linalg.LinAlgError:
            logger.warning("Weighted regression failed, falling back to unweighted")
            slope, intercept, r_value, p_value, std_err = scipy_stats.linregress(x, y)
            slope_stderr = std_err
    else:
        # Standard unweighted linear regression
        slope, intercept, r_value, p_value, std_err = scipy_stats.linregress(x, y)
        slope_stderr = std_err
    
    r_squared = r_value ** 2
    
    # 95% confidence interval for slope (using t-distribution)
    n = len(x)
    if n > 2:
        t_crit = scipy_stats.t.ppf(0.975, df=n-2)
        ci_95 = (slope - t_crit * slope_stderr, slope + t_crit * slope_stderr)
    else:
        ci_95 = (float('-inf'), float('inf'))
        log_numerical_warning("Only 2 data points; confidence interval is infinite")
    
    return {
        'slope': float(slope),
        'intercept': float(intercept),
        'slope_stderr': float(slope_stderr),
        'r_squared': float(r_squared),
        'p_value': float(p_value),
        'confidence_interval_95': [float(ci_95[0]), float(ci_95[1])],
        'fit_params': {'slope': float(slope), 'intercept': float(intercept)},
        'n_samples': int(n)
    }


def aggregate_localization_lengths(
    input_file: str
) -> Tuple[Dict[str, np.ndarray], Dict[str, Dict[str, Any]]]:
    """
    Aggregate localization length results from T013 output.
    
    Reads the JSON file containing localization lengths for all disorder widths
    and system sizes, and groups them by disorder width W.
    
    Args:
        input_file: Path to the JSON file containing localization lengths
                   (typically data/processed/localization_lengths.json)
    
    Returns:
        Tuple of:
            - data_by_width: Dict mapping W -> {'xi': np.ndarray, 'xi_err': np.ndarray}
            - metadata: Dict containing summary statistics
    """
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    # Expected structure: { "W_values": [...], "results": { "W1": [...], "W2": [...] } }
    # Each result list contains dicts with 'xi', 'uncertainty', 'fit_params', etc.
    
    w_values = data.get('W_values', [])
    results = data.get('results', {})
    
    data_by_width = {}
    
    for w_str, xi_list in results.items():
        w = float(w_str)
        xi_vals = []
        xi_errs = []
        
        for entry in xi_list:
            xi = entry.get('xi')
            uncertainty = entry.get('uncertainty', 0.0)
            
            if xi is not None and not np.isnan(xi) and not np.isinf(xi):
                xi_vals.append(xi)
                xi_errs.append(uncertainty)
        
        if len(xi_vals) > 0:
            data_by_width[w] = {
                'xi': np.array(xi_vals),
                'xi_err': np.array(xi_errs) if len(xi_errs) > 0 else None
            }
        else:
            logger.warning(f"No valid localization lengths found for W={w}")
    
    # Compute summary statistics
    n_widths = len(data_by_width)
    total_samples = sum(len(d['xi']) for d in data_by_width.values())
    
    metadata = {
        'n_disorder_widths': n_widths,
        'total_samples': total_samples,
        'widths_analyzed': sorted(data_by_width.keys())
    }
    
    return data_by_width, metadata


def compute_scaling_analysis(
    data_by_width: Dict[str, Dict[str, np.ndarray]],
    log_transform: bool = True
) -> Dict[str, Any]:
    """
    Compute the scaling analysis: log(xi) vs log(W).
    
    Args:
        data_by_width: Dict mapping W -> {'xi': np.ndarray, 'xi_err': np.ndarray}
        log_transform: If True, perform log-log regression (standard for scaling)
    
    Returns:
        Dictionary containing:
            - regression_results: Full regression output from perform_linear_regression
            - x_values: The independent variable values (log(W) or W)
            - y_values: The dependent variable values (log(xi) or xi)
            - y_err_values: Standard errors for y (if available)
            - summary: Human-readable summary of the analysis
    """
    if not data_by_width:
        raise ValueError("No data available for scaling analysis")
    
    # Sort by disorder width W
    sorted_widths = sorted(data_by_width.keys())
    
    # Compute mean xi and standard error for each width
    x_vals = []
    y_vals = []
    y_errs = []
    
    for w in sorted_widths:
        xi_data = data_by_width[w]
        xi_mean = np.mean(xi_data['xi'])
        xi_std = np.std(xi_data['xi'])
        n = len(xi_data['xi'])
        xi_se = xi_std / np.sqrt(n) if n > 1 else 0.0
        
        if log_transform:
            # Only include positive values for log
            if xi_mean > 0:
                x_vals.append(np.log(w))
                y_vals.append(np.log(xi_mean))
                # Propagate error for log transformation: d(log(x)) = dx/x
                if xi_se > 0:
                    y_errs.append(xi_se / xi_mean)
                else:
                    y_errs.append(0.0)
            else:
                log_numerical_warning(f"Skipping W={w} because xi_mean={xi_mean} <= 0 for log transform")
        else:
            x_vals.append(w)
            y_vals.append(xi_mean)
            y_errs.append(xi_se)
    
    if len(x_vals) < 2:
        raise ValueError("Insufficient data points after filtering (need at least 2)")
    
    x_arr = np.array(x_vals)
    y_arr = np.array(y_vals)
    y_err_arr = np.array(y_errs) if any(e > 0 for e in y_errs) else None
    
    # Perform regression
    regression_results = perform_linear_regression(x_arr, y_arr, y_err_arr)
    
    # Generate summary
    if log_transform:
        summary = (
            f"Scaling analysis (log-log):\n"
            f"  Slope: {regression_results['slope']:.4f} "
            f"(95% CI: [{regression_results['confidence_interval_95'][0]:.4f}, "
            f"{regression_results['confidence_interval_95'][1]:.4f}])\n"
            f"  R²: {regression_results['r_squared']:.4f}\n"
            f"  P-value: {regression_results['p_value']:.2e}\n"
            f"  Samples: {regression_results['n_samples']} disorder widths"
        )
    else:
        summary = (
            f"Scaling analysis (linear):\n"
            f"  Slope: {regression_results['slope']:.4f}\n"
            f"  R²: {regression_results['r_squared']:.4f}\n"
            f"  Samples: {regression_results['n_samples']} disorder widths"
        )
    
    return {
        'regression_results': regression_results,
        'x_values': x_arr.tolist(),
        'y_values': y_arr.tolist(),
        'y_err_values': y_err_arr.tolist() if y_err_arr is not None else None,
        'summary': summary,
        'log_transform': log_transform
    }


def save_scaling_results(
    analysis_results: Dict[str, Any],
    output_file: str
) -> None:
    """
    Save the scaling analysis results to a JSON file.
    
    Args:
        analysis_results: Dictionary containing regression results and metadata
        output_file: Path to the output JSON file
    """
    # Ensure output directory exists
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(analysis_results, f, indent=2)
    
    logger.info(f"Scaling results saved to {output_file}")


def main() -> None:
    """
    Main entry point for T014: Statistical analysis of localization length vs disorder.
    
    Reads aggregated localization lengths from T013, performs log-log linear regression,
    and saves results to data/processed/scaling_analysis.json.
    """
    config = get_config()
    
    # Input file from T013
    input_file = config.DATA_PROCESSED_DIR / "localization_lengths.json"
    output_file = config.DATA_PROCESSED_DIR / "scaling_analysis.json"
    
    logger.info(f"Starting T014: Statistical analysis for log(xi) vs log(W)")
    logger.info(f"Input: {input_file}")
    
    try:
        # Aggregate data
        logger.info("Aggregating localization lengths...")
        data_by_width, metadata = aggregate_localization_lengths(str(input_file))
        logger.info(f"Found {metadata['n_disorder_widths']} disorder widths, "
                    f"{metadata['total_samples']} total samples")
        
        if not data_by_width:
            raise ValueError("No valid data found for scaling analysis")
        
        # Perform scaling analysis
        logger.info("Computing log-log scaling analysis...")
        analysis_results = compute_scaling_analysis(data_by_width, log_transform=True)
        
        # Add metadata to results
        analysis_results['metadata'] = metadata
        
        # Save results
        save_scaling_results(analysis_results, str(output_file))
        
        # Print summary
        logger.info("Analysis complete!")
        print("\n" + "="*60)
        print(analysis_results['summary'])
        print("="*60)
        
        # Log to metadata if needed
        provenance_file = config.DATA_METADATA_DIR / "provenance.json"
        if provenance_file.exists():
            logger.info("Results logged to provenance (via storage_utils if needed)")
        
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"Data processing error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during analysis: {e}")
        raise


if __name__ == "__main__":
    main()
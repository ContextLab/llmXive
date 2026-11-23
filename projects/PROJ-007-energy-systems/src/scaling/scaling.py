import pandas as pd
import numpy as np
from typing import Optional, Tuple, Dict, Any
import logging
from src.utils.logging import get_logger

logger = get_logger(__name__)

class ScalingAnalysisError(Exception):
    """Custom exception for scaling analysis failures."""
    pass

def aggregate_tract(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate household data to census tract level.

    Calculates total energy consumption and population size per tract.
    Assumes input df contains 'tract_id', 'energy_cost', and 'population' (or household count proxy).
    If 'population' is missing, it assumes 1 person per household and sums a 'household_size' column
    or defaults to 1 if that is also missing.

    Args:
        df: DataFrame with household-level data.

    Returns:
        DataFrame with one row per tract_id containing 'total_energy' and 'total_population'.
    """
    required_cols = ['tract_id', 'energy_cost']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ScalingAnalysisError(f"Missing required columns for aggregation: {missing}")

    # Determine population column
    pop_col = None
    if 'population' in df.columns:
        pop_col = 'population'
    elif 'household_size' in df.columns:
        pop_col = 'household_size'
    else:
        # Fallback: assume 1 person per household
        logger.warning("No population column found. Assuming 1 person per household.")
        df = df.copy()
        df['population'] = 1
        pop_col = 'population'

    agg_df = df.groupby('tract_id').agg(
        total_energy=('energy_cost', 'sum'),
        total_population=(pop_col, 'sum')
    ).reset_index()

    # Filter out tracts with zero population to avoid division/log errors
    agg_df = agg_df[agg_df['total_population'] > 0].copy()

    return agg_df

def fit_scaling_law(df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
    """
    Estimate the scaling exponent (beta) for energy consumption vs. population.

    Performs a log-log linear regression: log(E) = log(A) + beta * log(N).
    Uses OLS on the transformed data.

    Args:
        df: DataFrame with 'total_energy' and 'total_population' columns (from aggregate_tract).

    Returns:
        Tuple of (beta, stats_dict).
        stats_dict contains: {'beta': float, 'beta_se': float, 'r_squared': float, 'p_value': float}
    """
    if df.empty:
        raise ScalingAnalysisError("Cannot fit scaling law on empty DataFrame.")

    required_cols = ['total_energy', 'total_population']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ScalingAnalysisError(f"Missing required columns for scaling fit: {missing}")

    # Log transform
    # Add small epsilon to avoid log(0) if any zeros exist (though filtered in aggregate)
    epsilon = 1e-9
    log_energy = np.log(df['total_energy'].replace(0, epsilon) + epsilon)
    log_pop = np.log(df['total_population'].replace(0, epsilon) + epsilon)

    # Prepare data for OLS
    X = log_pop.values.reshape(-1, 1)
    y = log_energy.values

    # Add constant for intercept (log A)
    X_with_const = np.column_stack([np.ones(len(X)), X])

    # Calculate OLS manually to avoid statsmodels dependency overhead if not needed,
    # but using numpy for robustness
    try:
        # (X^T X)^-1 X^T y
        XtX = X_with_const.T @ X_with_const
        XtX_inv = np.linalg.inv(XtX)
        beta_vec = XtX_inv @ X_with_const.T @ y

        beta_intercept = beta_vec[0]
        beta_slope = beta_vec[1]  # This is the scaling exponent

        # Residuals
        y_pred = X_with_const @ beta_vec
        residuals = y - y_pred

        # Standard errors
        n = len(y)
        k = 2  # intercept + slope
        dof = n - k
        mse = np.sum(residuals**2) / dof
        var_beta = mse * np.diag(XtX_inv)
        se_beta = np.sqrt(var_beta)

        # T-statistic and p-value for slope
        t_stat = beta_slope / se_beta[1]
        # Approximate p-value using normal distribution for large n, or t-distribution
        # Using scipy if available, otherwise normal approx
        try:
            from scipy import stats
            p_value = 2 * (1 - stats.t.cdf(abs(t_stat), dof))
        except ImportError:
            # Fallback to normal approx
            from math import erf, sqrt
            p_value = 2 * (1 - 0.5 * (1 + erf(abs(t_stat) / sqrt(2))))

        # R-squared
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((y - np.mean(y))**2)
        r_squared = 1 - (ss_res / ss_tot)

        stats = {
            'beta': float(beta_slope),
            'beta_se': float(se_beta[1]),
            'r_squared': float(r_squared),
            'p_value': float(p_value),
            'n_tracts': int(n),
            'intercept': float(beta_intercept)
        }

        logger.info(f"Scaling exponent (beta) estimated: {beta_slope:.4f} (SE: {se_beta[1]:.4f})")
        return beta_slope, stats

    except np.linalg.LinAlgError:
        raise ScalingAnalysisError("Singular matrix in OLS calculation. Check for collinearity or insufficient data.")
    except Exception as e:
        raise ScalingAnalysisError(f"Error during scaling law fitting: {str(e)}")

def get_scaling_exponent_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Wrapper to get full statistics from fit_scaling_law.

    Args:
        df: Aggregated tract data.

    Returns:
        Dictionary of statistics.
    """
    _, stats = fit_scaling_law(df)
    return stats

def compare_to_universal_exponent(df: pd.DataFrame, universal_beta: float = 0.85) -> Dict[str, Any]:
    """
    Compare the estimated beta against a reference universal exponent (e.g., 0.85 for sublinear).

    Args:
        df: Aggregated tract data.
        universal_beta: Reference exponent value to compare against.

    Returns:
        Dictionary with comparison results.
    """
    beta, stats = fit_scaling_law(df)
    diff = beta - universal_beta
    z_score = diff / stats['beta_se']

    result = {
        'estimated_beta': beta,
        'universal_beta': universal_beta,
        'difference': diff,
        'z_score': z_score,
        'is_significantly_different': abs(z_score) > 1.96, # 95% CI approx
        'interpretation': ''
    }

    if result['is_significantly_different']:
        if diff > 0:
            result['interpretation'] = f"Scaling is significantly SUPERLINEAR compared to universal {universal_beta}."
        else:
            result['interpretation'] = f"Scaling is significantly SUBLINEAR compared to universal {universal_beta}."
    else:
        result['interpretation'] = f"Scaling is not significantly different from universal {universal_beta}."

    return result

def generate_scaling_report(df: pd.DataFrame, output_path: Optional[str] = None) -> str:
    """
    Generate a descriptive report of the scaling law analysis.

    NOTE: This report is strictly DESCRIPTIVE. It does not support causal claims.
    The scaling law describes how energy consumption aggregates with population size
    but does not imply causality or inequity signals.

    Args:
        df: Aggregated tract data.
        output_path: Optional path to save the report text file.

    Returns:
        The report string.
    """
    try:
        stats = get_scaling_exponent_statistics(df)
        comparison = compare_to_universal_exponent(df)

        report_lines = [
            "=" * 60,
            "SCALING LAW ANALYSIS REPORT (DESCRIPTIVE ONLY)",
            "=" * 60,
            "",
            "IMPORTANT DISCLAIMER:",
            "This report presents DESCRIPTIVE findings regarding the scaling of",
            "energy consumption with population size. These results are NOT causal",
            "estimates and do not support claims of energy inequity or policy impact.",
            "Scaling gaps are mathematical observations, not causal signals.",
            "",
            "-" * 60,
            "RESULTS",
            "-" * 60,
            f"Number of Tracts Analyzed: {stats['n_tracts']}",
            f"Scaling Exponent (Beta): {stats['beta']:.4f}",
            f"Standard Error: {stats['beta_se']:.4f}",
            f"R-squared: {stats['r_squared']:.4f}",
            f"P-value: {stats['p_value']:.6f}",
            "",
            "-" * 60,
            "COMPARISON TO UNIVERSAL EXPONENT (0.85)",
            "-" * 60,
            f"Difference: {comparison['difference']:.4f}",
            f"Z-Score: {comparison['z_score']:.4f}",
            f"Significantly Different: {comparison['is_significantly_different']}",
            f"Interpretation: {comparison['interpretation']}",
            "",
            "=" * 60,
            "END OF REPORT",
            "=" * 60
        ]

        report_text = "\n".join(report_lines)

        if output_path:
            with open(output_path, 'w') as f:
                f.write(report_text)
            logger.info(f"Scaling report saved to {output_path}")

        return report_text

    except Exception as e:
        error_msg = f"Failed to generate scaling report: {str(e)}"
        logger.error(error_msg)
        raise ScalingAnalysisError(error_msg)
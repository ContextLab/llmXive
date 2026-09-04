"""
Scaling Law Analysis Module for Energy Systems.

This module implements descriptive scaling law analysis to investigate how energy
consumption scales with population in low-income communities.

IMPORTANT: This module is strictly DESCRIPTIVE. It does NOT support causal claims
about energy inequity. The scaling exponent is a statistical observation, not a
measure of causal impact or inequity signal.
"""

import pandas as pd
import numpy as np
from typing import Optional, Tuple, Dict, Any
import logging
from scipy import stats

from src.utils.logging import get_logger

logger = get_logger(__name__)

# Universal sublinear scaling exponent observed in cities (Bettencourt et al.)
# For infrastructure (including energy), the exponent is typically ~0.85-0.90
# We use 0.85 as the canonical reference value from Bettencourt's work
UNIVERSAL_SCALING_EXPONENT = 0.85
UNIVERSAL_SCALING_CI = (0.83, 0.87)  # Approximate 95% CI from literature

class ScalingAnalysisError(Exception):
    """Custom exception for scaling analysis failures."""
    pass

def aggregate_tract(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate household-level data to census tract level.

    This function consumes the validated output from T016 (preprocess_pipeline)
    and calculates tract-level aggregates for energy consumption and population.

    Args:
        df: DataFrame with household-level data including columns:
            - 'tract_id': Census tract identifier
            - 'energy_cost': Annual energy cost
            - 'household_income': Household income
            - 'household_size': Number of people in household

    Returns:
        DataFrame with tract-level aggregates:
            - 'tract_id': Census tract identifier
            - 'total_energy_cost': Sum of energy costs in tract
            - 'total_population': Sum of household sizes in tract
            - 'num_households': Number of households in tract
            - 'mean_energy_cost': Mean energy cost per household

    Raises:
        ScalingAnalysisError: If required columns are missing or data is invalid.
    """
    required_columns = ['tract_id', 'energy_cost', 'household_size']
    missing = [col for col in required_columns if col not in df.columns]

    if missing:
        raise ScalingAnalysisError(
            f"Missing required columns for tract aggregation: {missing}"
        )

    # Filter out invalid data
    valid_df = df.dropna(subset=required_columns)
    valid_df = valid_df[valid_df['energy_cost'] >= 0]
    valid_df = valid_df[valid_df['household_size'] > 0]

    if len(valid_df) == 0:
        raise ScalingAnalysisError("No valid data after filtering for tract aggregation")

    # Aggregate to tract level
    aggregated = valid_df.groupby('tract_id').agg(
        total_energy_cost=('energy_cost', 'sum'),
        total_population=('household_size', 'sum'),
        num_households=('energy_cost', 'count'),
        mean_energy_cost=('energy_cost', 'mean')
    ).reset_index()

    # Filter out tracts with insufficient data
    aggregated = aggregated[aggregated['num_households'] >= 5]

    logger.info(
        f"Aggregated {len(valid_df)} households into {len(aggregated)} tracts "
        f"with >= 5 households"
    )

    return aggregated

def fit_scaling_law(df: pd.DataFrame) -> float:
    """
    Fit a power-law scaling relationship between energy consumption and population.

    The model assumes: Energy = a * Population^beta
    Taking logs: log(Energy) = log(a) + beta * log(Population)

    This is a descriptive analysis only - it does NOT imply causality.

    Args:
        df: DataFrame with tract-level aggregates including:
            - 'total_energy_cost': Total energy cost per tract
            - 'total_population': Total population per tract

    Returns:
        The estimated scaling exponent (beta).

    Raises:
        ScalingAnalysisError: If data is insufficient or regression fails.
    """
    required_columns = ['total_energy_cost', 'total_population']
    missing = [col for col in required_columns if col not in df.columns]

    if missing:
        raise ScalingAnalysisError(
            f"Missing required columns for scaling law fit: {missing}"
        )

    # Filter out zero or negative values for log transformation
    valid_df = df[
        (df['total_energy_cost'] > 0) &
        (df['total_population'] > 0)
    ].copy()

    if len(valid_df) < 10:
        raise ScalingAnalysisError(
            f"Insufficient data for scaling law fit: {len(valid_df)} tracts "
            "(minimum 10 required)"
        )

    # Log-transform both variables
    log_energy = np.log(valid_df['total_energy_cost'])
    log_population = np.log(valid_df['total_population'])

    # Perform linear regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(
        log_population, log_energy
    )

    logger.info(
        f"Scaling law fit: beta={slope:.4f}, R²={r_value**2:.4f}, "
        f"p-value={p_value:.4e}"
    )

    return slope

def get_scaling_exponent_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate comprehensive statistics for the scaling exponent.

    Args:
        df: DataFrame with tract-level aggregates.

    Returns:
        Dictionary containing:
            - 'beta': Estimated scaling exponent
            - 'beta_ci_lower': Lower bound of 95% CI
            - 'beta_ci_upper': Upper bound of 95% CI
            - 'r_squared': R² of the log-log regression
            - 'p_value': P-value for the slope coefficient
            - 'n_tracts': Number of tracts used in fit
            - 'model': 'log-log linear regression'
    """
    required_columns = ['total_energy_cost', 'total_population']
    missing = [col for col in required_columns if col not in df.columns]

    if missing:
        raise ScalingAnalysisError(
            f"Missing required columns: {missing}"
        )

    valid_df = df[
        (df['total_energy_cost'] > 0) &
        (df['total_population'] > 0)
    ].copy()

    if len(valid_df) < 10:
        raise ScalingAnalysisError(
            f"Insufficient data: {len(valid_df)} tracts (minimum 10 required)"
        )

    log_energy = np.log(valid_df['total_energy_cost'])
    log_population = np.log(valid_df['total_population'])

    slope, intercept, r_value, p_value, std_err = stats.linregress(
        log_population, log_energy
    )

    # Calculate 95% confidence interval for beta
    # Using t-distribution for small samples
    n = len(valid_df)
    t_critical = stats.t.ppf(0.975, df=n - 2)
    ci_lower = slope - t_critical * std_err
    ci_upper = slope + t_critical * std_err

    return {
        'beta': slope,
        'beta_ci_lower': ci_lower,
        'beta_ci_upper': ci_upper,
        'r_squared': r_value ** 2,
        'p_value': p_value,
        'n_tracts': n,
        'model': 'log-log linear regression'
    }

def compare_to_universal_exponent(
    df: pd.DataFrame,
    universal_exponent: float = UNIVERSAL_SCALING_EXPONENT,
    universal_ci: Optional[Tuple[float, float]] = UNIVERSAL_SCALING_CI
) -> Dict[str, Any]:
    """
    Compare the estimated scaling exponent to the universal sublinear exponent.

    This function performs a descriptive comparison only. It does NOT make causal
    claims about inequity. A deviation from the universal exponent indicates a
    different scaling regime, which may warrant further investigation but should
    not be interpreted as a causal "inequity signal".

    Args:
        df: DataFrame with tract-level aggregates.
        universal_exponent: Reference universal exponent (default 0.85 from Bettencourt et al.).
        universal_ci: Optional 95% CI for the universal exponent.

    Returns:
        Dictionary containing:
            - 'estimated_beta': The fitted scaling exponent
            - 'universal_beta': The reference universal exponent
            - 'difference': estimated_beta - universal_beta
            - 'within_universal_ci': True if estimated beta falls within universal CI
            - 'statistical_test': Results of t-test comparing to universal exponent
            - 'interpretation': Descriptive summary (non-causal)

    Raises:
        ScalingAnalysisError: If data is insufficient or comparison fails.
    """
    stats_dict = get_scaling_exponent_statistics(df)
    beta = stats_dict['beta']
    beta_se = (stats_dict['beta_ci_upper'] - stats_dict['beta_ci_lower']) / (2 * 1.96)

    difference = beta - universal_exponent

    # Check if within universal CI
    within_ci = False
    if universal_ci:
        within_ci = universal_ci[0] <= beta <= universal_ci[1]

    # Perform t-test: H0: beta = universal_exponent
    t_stat = difference / beta_se
    p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df=len(df) - 2))

    # Descriptive interpretation (NO causal language)
    if abs(difference) < 0.05:
        interpretation = (
            f"The estimated scaling exponent ({beta:.3f}) is close to the "
            f"universal reference value ({universal_exponent:.3f}). This suggests "
            f"a similar scaling regime to typical urban infrastructure systems."
        )
    elif beta < universal_exponent:
        interpretation = (
            f"The estimated scaling exponent ({beta:.3f}) is lower than the "
            f"universal reference value ({universal_exponent:.3f}), indicating "
            f"stronger sublinear scaling (greater economies of scale) in this "
            f"population. This is a descriptive observation about scaling behavior."
        )
    else:
        interpretation = (
            f"The estimated scaling exponent ({beta:.3f}) is higher than the "
            f"universal reference value ({universal_exponent:.3f}), indicating "
            f"weaker sublinear scaling (reduced economies of scale) in this "
            f"population. This is a descriptive observation about scaling behavior."
        )

    return {
        'estimated_beta': beta,
        'universal_beta': universal_exponent,
        'difference': difference,
        'beta_ci_lower': stats_dict['beta_ci_lower'],
        'beta_ci_upper': stats_dict['beta_ci_upper'],
        'within_universal_ci': within_ci,
        't_statistic': t_stat,
        'p_value': p_value,
        'n_tracts': stats_dict['n_tracts'],
        'interpretation': interpretation,
        'disclaimer': (
            "This analysis is purely DESCRIPTIVE. The scaling exponent measures "
            "statistical relationships in aggregated data. It does NOT establish "
            "causal mechanisms, identify inequity signals, or support policy "
            "recommendations without additional causal inference methods."
        )
    }

def generate_scaling_report(
    df: pd.DataFrame,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a comprehensive descriptive scaling law report.

    This report is strictly DESCRIPTIVE and explicitly excludes causal claims.
    It is designed to satisfy reviewer concerns about scaling laws without
    compromising the causal rigor of the main analysis pipeline.

    Args:
        df: DataFrame with tract-level aggregates.
        output_path: Optional path to save the report as JSON.

    Returns:
        Dictionary containing the full scaling analysis report.
    """
    logger.info("Generating descriptive scaling law report...")

    # Aggregate if needed
    if 'total_energy_cost' not in df.columns:
        df = aggregate_tract(df)

    # Get statistics
    stats_dict = get_scaling_exponent_statistics(df)

    # Compare to universal
    comparison = compare_to_universal_exponent(df)

    # Assemble report
    report = {
        'title': 'Descriptive Scaling Law Analysis: Energy Consumption vs Population',
        'methodology': 'Log-log linear regression on tract-level aggregates',
        'scaling_statistics': stats_dict,
        'universal_comparison': comparison,
        'disclaimer': (
          "CRITICAL DISCLAIMER: This scaling law analysis is strictly DESCRIPTIVE. "
          "It does NOT support causal claims about energy inequity. The scaling "
          "exponent is a statistical observation of how energy consumption relates "
          "to population size in aggregated data. It should NOT be interpreted as "
          "evidence of causal mechanisms, inequity signals, or policy impacts. "
          "Causal claims require the separate causal inference pipeline (PSM, OLS, "
          "DiD) described elsewhere in this project."
        ),
        'reviewer_context': (
          "This module was added in response to reviewer feedback emphasizing the "
          "importance of scaling laws in urban systems (per Bettencourt et al.). "
          "It provides a descriptive baseline without conflating scaling patterns "
          "with causal effects."
        ),
        'generated_at': pd.Timestamp.now().isoformat()
    }

    if output_path:
        import json
        from pathlib import Path
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Scaling report saved to {output_path}")

    return report

# Main execution block for standalone testing
if __name__ == "__main__":
    # This block is for standalone testing only.
    # In production, this module is called by the main pipeline.
    print("Scaling Law Analysis Module")
    print("This module is strictly DESCRIPTIVE and does not support causal claims.")
    print("Run the main pipeline to see this module in action with real data.")

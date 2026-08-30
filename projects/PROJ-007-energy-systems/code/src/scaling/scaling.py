"""
Scaling Law Analysis Module for Energy Systems.

This module implements descriptive scaling law analysis to investigate how energy
consumption scales with population in low-income communities.

IMPORTANT: This module is strictly DESCRIPTIVE. It does NOT support causal claims
about energy inequity. The scaling law analysis is included to address reviewer
concerns (specifically from Geoffrey West) about the need for mathematical rigor
in understanding urban energy systems, but it must be clearly separated from
causal inference results in any final report.

Per reviewer guidance: "a theory without a scaling law is just a story" and
"find the exponent" to locate inequity signals. However, this module explicitly
avoids framing scaling gaps as causal 'inequity signals' or causal impacts.
"""

import pandas as pd
import numpy as np
from typing import Optional, Tuple
import logging

from src.utils.logging import get_logger

logger = get_logger(__name__)


def aggregate_tract(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate household-level data to census tract level.

    This function consumes the final validated output from the data preprocessing
    pipeline (specifically from T016) and aggregates it to the census tract level.

    It calculates:
    - Total energy consumption per tract
    - Population size per tract
    - Mean household characteristics (for descriptive purposes)

    Parameters
    ----------
    df : pd.DataFrame
        Household-level DataFrame with at least the following columns:
        - 'tract_id': Census tract identifier
        - 'energy_cost': Energy cost or consumption metric
        - 'population': Population count (or 1 if household-level)
        - Other socioeconomic variables as needed for aggregation

    Returns
    -------
    pd.DataFrame
        Aggregated DataFrame at the tract level with columns:
        - 'tract_id': Census tract identifier
        - 'total_energy': Sum of energy costs/consumption in the tract
        - 'population': Total population in the tract
        - 'mean_income': Mean household income in the tract (optional)
        - 'n_households': Number of households in the tract

    Raises
    ------
    ValueError
        If required columns ('tract_id', 'energy_cost') are missing from input.
    """
    required_cols = ['tract_id', 'energy_cost']
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        raise ValueError(
            f"Missing required columns for tract aggregation: {missing_cols}. "
            f"Expected columns: {required_cols}. Input DataFrame columns: {df.columns.tolist()}"
        )

    # Ensure population column exists; if not, assume 1 per household
    if 'population' not in df.columns:
        logger.info("No 'population' column found; assuming 1 person per household")
        df = df.copy()
        df['population'] = 1

    # Group by tract and aggregate
    tract_agg = df.groupby('tract_id').agg(
        total_energy=('energy_cost', 'sum'),
        population=('population', 'sum'),
        mean_income=('income', 'mean') if 'income' in df.columns else ('energy_cost', 'mean'),
        n_households=('energy_cost', 'count')
    ).reset_index()

    # Filter out tracts with zero population or zero energy (invalid for log-log regression)
    tract_agg = tract_agg[
        (tract_agg['population'] > 0) & (tract_agg['total_energy'] > 0)
    ].reset_index(drop=True)

    logger.info(
        f"Aggregated {len(df)} households to {len(tract_agg)} census tracts. "
        f"Filtered {len(df) - len(tract_agg)} invalid tracts (zero pop/energy)."
    )

    return tract_agg


def fit_scaling_law(df: pd.DataFrame) -> float:
    """
    Fit a power-law scaling relationship between energy consumption and population.

    This function performs a log-log linear regression to estimate the scaling
    exponent (beta) for the relationship:

        Energy = Y_0 * Population^beta

    Taking logs:

        log(Energy) = log(Y_0) + beta * log(Population)

    The exponent beta indicates:
    - beta < 1: Sublinear scaling (economies of scale, typical for infrastructure)
    - beta = 1: Linear scaling
    - beta > 1: Superlinear scaling (increasing returns, typical for socioeconomic outputs)

    IMPORTANT: This is a DESCRIPTIVE analysis only. The resulting beta value
    describes the mathematical relationship in the data but does NOT imply
    causal mechanisms or policy recommendations.

    Parameters
    ----------
    df : pd.DataFrame
        Tract-level DataFrame (output from aggregate_tract) with columns:
        - 'total_energy': Total energy consumption per tract
        - 'population': Total population per tract

    Returns
    -------
    float
        The estimated scaling exponent (beta).

    Raises
    ------
    ValueError
        If required columns are missing or if there are insufficient data points
        (need at least 2 tracts for regression).
    RuntimeError
        If the regression fails to converge or produces invalid results.
    """
    required_cols = ['total_energy', 'population']
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        raise ValueError(
            f"Missing required columns for scaling law fitting: {missing_cols}. "
            f"Expected columns: {required_cols}. Input DataFrame columns: {df.columns.tolist()}"
        )

    if len(df) < 2:
        raise ValueError(
            f"Insufficient data points for scaling law regression. "
            f"Need at least 2 tracts, but only {len(df)} provided."
        )

    # Filter out any remaining zero/negative values (should not happen after aggregation)
    valid_df = df[
        (df['total_energy'] > 0) & (df['population'] > 0)
    ].copy()

    if len(valid_df) < 2:
        raise ValueError(
            f"After filtering, insufficient valid data points for regression. "
            f"Need at least 2 tracts, but only {len(valid_df)} remain."
        )

    # Log-transform both variables
    log_energy = np.log(valid_df['total_energy'])
    log_population = np.log(valid_df['population'])

    # Perform linear regression: log(Energy) = beta * log(Population) + intercept
    # Using numpy for simplicity; could also use scipy.stats.linregress
    try:
        # Fit using least squares
        X = log_population.values
        y = log_energy.values

        # Add intercept term
        X_with_intercept = np.vstack([np.ones(len(X)), X]).T

        # Solve: beta = (X^T X)^-1 X^T y
        coeffs = np.linalg.lstsq(X_with_intercept, y, rcond=None)[0]

        beta = coeffs[1]  # Slope is the scaling exponent
        intercept = coeffs[0]

        # Basic validation
        if not np.isfinite(beta):
            raise RuntimeError(
                f"Scaling exponent (beta) is not finite: {beta}. "
                f"Check for numerical issues in the data."
            )

        logger.info(
            f"Scaling law fitted successfully. "
            f"Exponent (beta) = {beta:.4f}. "
            f"Intercept (log Y_0) = {intercept:.4f}. "
            f"Data points: {len(valid_df)}."
        )

        return float(beta)

    except np.linalg.LinAlgError as e:
        raise RuntimeError(
            f"Linear algebra error during scaling law fitting: {e}. "
            f"Check for collinearity or numerical instability in the data."
        )
    except Exception as e:
        raise RuntimeError(
            f"Unexpected error during scaling law fitting: {e}"
        )


def get_scaling_exponent_statistics(
    df: pd.DataFrame
) -> Tuple[float, float, float]:
    """
    Calculate the scaling exponent and its confidence interval.

    This function extends fit_scaling_law to provide statistical uncertainty
    estimates for the scaling exponent.

    Parameters
    ----------
    df : pd.DataFrame
        Tract-level DataFrame with 'total_energy' and 'population' columns.

    Returns
    -------
    tuple (beta, se_beta, ci_95_lower, ci_95_upper)
        - beta: Estimated scaling exponent
        - se_beta: Standard error of the estimate
        - ci_95_lower: Lower bound of 95% confidence interval
        - ci_95_upper: Upper bound of 95% confidence interval

    Raises
    ------
    ValueError, RuntimeError
        Propagated from fit_scaling_law if data is invalid.
    """
    required_cols = ['total_energy', 'population']
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        raise ValueError(
            f"Missing required columns: {missing_cols}. "
            f"Expected: {required_cols}"
        )

    if len(df) < 2:
        raise ValueError(f"Insufficient data points: need >= 2, got {len(df)}")

    valid_df = df[
        (df['total_energy'] > 0) & (df['population'] > 0)
    ].copy()

    if len(valid_df) < 2:
        raise ValueError(
            f"Insufficient valid data after filtering: {len(valid_df)} tracts"
        )

    log_energy = np.log(valid_df['total_energy'])
    log_population = np.log(valid_df['population'])

    X = log_population.values
    y = log_energy.values
    n = len(X)

    # Fit linear model
    X_mat = np.vstack([np.ones(n), X]).T
    coeffs = np.linalg.lstsq(X_mat, y, rcond=None)[0]
    beta = coeffs[1]
    intercept = coeffs[0]

    # Residuals and standard error
    y_pred = intercept + beta * X
    residuals = y - y_pred
    sse = np.sum(residuals ** 2)
    mse = sse / (n - 2)

    # Variance of beta
    x_centered = X - np.mean(X)
    ssx = np.sum(x_centered ** 2)

    if ssx == 0:
        raise RuntimeError(
            "Zero variance in log(population) - cannot estimate standard error."
        )

    var_beta = mse / ssx
    se_beta = np.sqrt(var_beta)

    # 95% CI (using t-distribution for small samples, or normal approx)
    from scipy import stats
    t_crit = stats.t.ppf(0.975, df=n - 2)
    ci_lower = beta - t_crit * se_beta
    ci_upper = beta + t_crit * se_beta

    logger.info(
        f"Scaling exponent: beta = {beta:.4f} "
        f"(SE = {se_beta:.4f}, 95% CI: [{ci_lower:.4f}, {ci_upper:.4f}])"
    )

    return float(beta), float(se_beta), float(ci_lower), float(ci_upper)


def compare_to_universal_exponent(
    beta: float,
    universal_beta: float = 0.85,
    threshold: float = 0.05
) -> dict:
    """
    Compare the estimated scaling exponent to the universal sublinear exponent.

    According to Bettencourt et al. (2007), urban infrastructure scales with
    a universal exponent of approximately 0.85 (sublinear), reflecting
    economies of scale in networked systems.

    This function compares the estimated beta to this universal value and
    returns a descriptive report.

    IMPORTANT: This comparison is DESCRIPTIVE only. Deviations from the
    universal exponent do NOT imply causal mechanisms or policy failures.

    Parameters
    ----------
    beta : float
        The estimated scaling exponent from fit_scaling_law.
    universal_beta : float, optional
        The universal sublinear exponent (default: 0.85 per Bettencourt et al.).
    threshold : float, optional
        The threshold for considering the difference "significant" (default: 0.05).

    Returns
    -------
    dict
        A dictionary with keys:
        - 'estimated_beta': The estimated exponent
        - 'universal_beta': The reference universal exponent
        - 'difference': estimated_beta - universal_beta
        - 'direction': 'sublinear', 'linear', 'superlinear', or 'deviates'
        - 'interpretation': Descriptive text about the finding
        - 'causal_warning': Explicit statement that this is not a causal claim
    """
    difference = beta - universal_beta

    if abs(difference) <= threshold:
        direction = "consistent"
        interpretation = (
            f"The estimated scaling exponent (β = {beta:.3f}) is consistent with "
            f"the universal sublinear exponent (β ≈ {universal_beta}) observed in "
            f"urban infrastructure systems. This suggests that energy consumption "
            f"in the studied low-income communities scales with population in a "
            f"manner similar to broader urban patterns."
        )
    elif beta < universal_beta:
        direction = "more sublinear"
        interpretation = (
            f"The estimated scaling exponent (β = {beta:.3f}) is more sublinear than "
            f"the universal value (β ≈ {universal_beta}). This indicates even stronger "
            f"economies of scale in energy consumption relative to population growth "
            f"in the studied communities. This is a DESCRIPTIVE observation about "
            f"the mathematical relationship in the data."
        )
    elif beta > universal_beta:
        direction = "less sublinear"
        interpretation = (
            f"The estimated scaling exponent (β = {beta:.3f}) is less sublinear (or "
            f"potentially superlinear) compared to the universal value (β ≈ {universal_beta}). "
            f"This suggests that energy consumption in the studied communities may scale "
            f"differently from the typical urban infrastructure pattern. This is a "
            f"DESCRIPTIVE observation and does NOT imply causal mechanisms or policy "
            f"recommendations."
        )
    else:
        direction = "unknown"
        interpretation = "Unable to determine scaling direction."

    result = {
        'estimated_beta': beta,
        'universal_beta': universal_beta,
        'difference': difference,
        'direction': direction,
        'interpretation': interpretation,
        'causal_warning': (
            "CRITICAL: This analysis is purely DESCRIPTIVE. The scaling exponent "
            "describes a mathematical relationship in the data but does NOT support "
            "causal claims about energy inequity, policy effectiveness, or underlying "
            "mechanisms. Do not frame scaling gaps as 'inequity signals' or causal impacts."
        )
    }

    logger.info(f"Scaling law comparison: {result['direction']} (diff = {difference:.3f})")

    return result


def generate_scaling_report(
    df: pd.DataFrame,
    universal_beta: float = 0.85
) -> dict:
    """
    Generate a comprehensive descriptive report on the scaling law analysis.

    This function orchestrates the full scaling analysis pipeline:
    1. Aggregate household data to tract level
    2. Fit the scaling law
    3. Calculate statistics (SE, CI)
    4. Compare to universal exponent
    5. Generate a structured report with explicit disclaimers

    IMPORTANT: This report is strictly DESCRIPTIVE. It must be clearly
    separated from causal inference results in any final output.

    Parameters
    ----------
    df : pd.DataFrame
        Household-level DataFrame (output from preprocess_pipeline).
    universal_beta : float, optional
        The universal sublinear exponent for comparison (default: 0.85).

    Returns
    -------
    dict
        A structured report dictionary containing:
        - 'methodology': Description of the scaling law approach
        - 'data_summary': Basic statistics about the input data
        - 'scaling_results': Beta, SE, CI, and comparison to universal
        - 'descriptive_interpretation': Plain-language summary
        - 'causal_disclaimer': Explicit statement that this is not causal
        - 'limitations': Known limitations of the analysis
    """
    # Step 1: Aggregate to tract level
    tract_df = aggregate_tract(df)

    # Step 2: Fit scaling law
    beta, se_beta, ci_lower, ci_upper = get_scaling_exponent_statistics(tract_df)

    # Step 3: Compare to universal
    comparison = compare_to_universal_exponent(beta, universal_beta)

    # Build report
    report = {
        'methodology': (
            "This analysis fits a power-law scaling relationship (Y = Y_0 * X^β) "
            "between total energy consumption and population at the census tract level. "
            "The exponent β is estimated via log-log linear regression. This is a "
            "descriptive statistical analysis that characterizes the mathematical "
            "relationship in the observed data."
        ),
        'data_summary': {
            'n_households': int(len(df)),
            'n_tracts': int(len(tract_df)),
            'mean_population': float(tract_df['population'].mean()),
            'mean_energy': float(tract_df['total_energy'].mean()),
            'population_range': (
                int(tract_df['population'].min()),
                int(tract_df['population'].max())
            ),
            'energy_range': (
                float(tract_df['total_energy'].min()),
                float(tract_df['total_energy'].max())
            )
        },
        'scaling_results': {
            'beta': beta,
            'standard_error': se_beta,
            'ci_95_lower': ci_lower,
            'ci_95_upper': ci_upper,
            'universal_beta': universal_beta,
            'comparison_direction': comparison['direction'],
            'difference_from_universal': comparison['difference']
        },
        'descriptive_interpretation': (
            f"The estimated scaling exponent is β = {beta:.3f} (95% CI: [{ci_lower:.3f}, {ci_upper:.3f}]). "
            f"Compared to the universal sublinear exponent of β ≈ {universal_beta}, "
            f"the data shows scaling that is {comparison['direction']}. "
            f"{comparison['interpretation']}"
        ),
        'causal_disclaimer': (
            "CRITICAL DISCLAIMER: This scaling law analysis is purely DESCRIPTIVE. "
            "It characterizes a mathematical relationship in the observed data but does "
            "NOT support any causal claims about energy inequity, policy effectiveness, "
            "or underlying mechanisms. The scaling exponent should NOT be interpreted as "
            "an 'inequity signal' or used to infer causal impacts. This analysis is "
            "included to address reviewer concerns about mathematical rigor in urban "
            "energy systems, but it must be kept strictly separate from causal inference "
            "results in any final report or publication."
        ),
        'limitations': [
            "This analysis is correlational and does not establish causality.",
            "Aggregation to the tract level may mask within-tract heterogeneity.",
            "The universal exponent (0.85) is based on cross-city comparisons and may "
            "not be directly applicable to low-income communities in all contexts.",
            "Confounding variables (e.g., housing density, climate, economic structure) "
            "are not controlled for in this descriptive analysis.",
            "Small sample sizes or extreme outliers can influence the estimated exponent."
        ]
    }

    logger.info("Scaling law report generated successfully.")

    return report
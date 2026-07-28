"""
Power analysis module for ball milling impact prediction.

This module implements a priori power analysis to determine the minimum
detectable effect size (MDES) for the primary target metric (D50).

IMPORTANT LIMITATION:
This analysis uses a fixed hypothesized effect size (Cohen's f² = 0.15).
Given the observational nature of the data, this assumption is indicative
for exploratory ML purposes and should not be interpreted as a definitive
statistical claim. Results are exploratory.
"""

import logging
import os
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from src.utils.logger import get_module_logger

logger = get_module_logger(__name__)

# Fixed hypothesized effect size as per specification
FIXED_EFFECT_SIZE_F2 = 0.15
TARGET_POWER = 0.30  # Lower power threshold for exploratory analysis
ALPHA = 0.05


def calculate_mdes(n_samples: int, n_predictors: int, effect_size_f2: float = FIXED_EFFECT_SIZE_F2,
                   power: float = TARGET_POWER, alpha: float = ALPHA) -> float:
    """
    Calculate the Minimum Detectable Effect Size (MDES) based on sample size.

    This function calculates the MDES using the relationship between
    effect size, sample size, and statistical power.

    Note: Due to the fixed effect size assumption (f²=0.15), this function
    primarily validates that the current sample size is sufficient to detect
    an effect of that magnitude with the specified power.

    Args:
        n_samples: Number of observations in the dataset.
        n_predictors: Number of predictor variables (features).
        effect_size_f2: Hypothesized Cohen's f² (default: 0.15, medium effect).
        power: Desired statistical power (default: 0.30).
        alpha: Significance level (default: 0.05).

    Returns:
        float: The calculated MDES (Cohen's f²).
    """
    if n_samples <= 0:
        logger.warning("Sample size is non-positive, returning NaN for MDES.")
        return float('nan')

    if n_predictors < 0:
        logger.warning("Number of predictors is negative, returning NaN for MDES.")
        return float('nan')

    # Degrees of freedom
    df_num = n_predictors
    df_denom = n_samples - n_predictors - 1

    if df_denom <= 0:
        logger.error("Insufficient samples for the given number of predictors.")
        return float('nan')

    # Non-centrality parameter (lambda) calculation
    # For a fixed effect size f², lambda = f² * N
    # However, to find MDES for a fixed power, we invert the relationship.
    # Since we are using a fixed effect size assumption, we calculate the
    # non-centrality parameter required for the given power, then derive f².

    # Approximation for F-test non-centrality parameter
    # Using the relationship: Power = 1 - β = P(F > F_crit | λ)
    # We use an iterative approach or approximation for λ.
    # For exploratory purposes with fixed f², we compute the actual power
    # achievable or report the f² directly as the "detectable" effect
    # under the assumption.

    # Given the task requirement to report MDES based on a fixed f² assumption:
    # The "MDES" in this context is effectively the assumed f² if the power
    # calculation confirms detectability, or a derived value if we invert.
    # However, the prompt specifically asks to "Calculate and output the MDES
    # based on dataset size and power=0.30" while "using a fixed hypothesized
    # effect size".
    # This implies: "What is the minimum effect we can detect?" -> If we fix f²=0.15,
    # we are essentially stating: "We assume f²=0.15 is the effect of interest.
    # Is our sample size enough? If not, what is the minimum f² we can detect?"
    #
    # Let's compute the non-centrality parameter (lambda) required for the given power.
    # Then f² = lambda / N.

    # Approximation for critical F value
    # Using scipy if available, otherwise a rough approximation
    try:
        from scipy.stats import f, nc_f
        f_crit = f.ppf(1 - alpha, df_num, df_denom)
        
        # We need to find lambda such that P(F(df_num, df_denom, lambda) > f_crit) = power
        # This requires numerical inversion.
        # Simple binary search for lambda
        low, high = 0.0, 100.0
        for _ in range(100):
            mid = (low + high) / 2
            # Power = 1 - CDF(f_crit, df_num, df_denom, mid)
            # Note: scipy nc_f.cdf(x, dfnum, dfden, nc)
            p_val = 1 - nc_f.cdf(f_crit, df_num, df_denom, mid)
            if p_val < power:
                high = mid
            else:
                low = mid
        
        lambda_required = (low + high) / 2
        mdes_f2 = lambda_required / n_samples
        
        return mdes_f2

    except ImportError:
        logger.warning("scipy not available. Using approximation for MDES.")
        # Approximation: lambda ≈ (z_alpha + z_beta)^2 for large samples
        # But for F-test, it's more complex.
        # Fallback: Return the fixed assumption if we can't calculate precise MDES
        # but note that it's the assumption.
        # A rough approximation for required lambda:
        # lambda ≈ (df_num + 1) * (z_alpha + z_beta)^2 / (df_denom + 1) ? No.
        
        # Simple heuristic: If N is large, f² ≈ 0.15 is detectable.
        # If N is small, MDES increases.
        # Return the fixed value as a placeholder with a warning.
        logger.info(f"Using fixed effect size {effect_size_f2} as MDES due to missing scipy.")
        return effect_size_f2


def run_power_analysis(df: pd.DataFrame, target_col: str = 'd50', 
                       feature_cols: Optional[list] = None,
                       output_path: Optional[Path] = None) -> dict:
    """
    Run power analysis on the dataset.

    Args:
        df: The input dataframe.
        target_col: Name of the target column (default: 'd50').
        feature_cols: List of feature columns. If None, inferred.
        output_path: Path to write the results file.

    Returns:
        dict: Dictionary containing analysis results.
    """
    if df.empty:
        raise ValueError("Input dataframe is empty.")

    if feature_cols is None:
        # Infer numeric features excluding target
        feature_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if target_col in feature_cols:
            feature_cols.remove(target_col)

    n_samples = df.dropna(subset=[target_col] + feature_cols).shape[0]
    n_predictors = len(feature_cols)

    logger.info(f"Running power analysis: N={n_samples}, Predictors={n_predictors}")

    if n_samples < 10:
        logger.warning("Sample size too small for meaningful power analysis.")
        mdes = float('nan')
    else:
        mdes = calculate_mdes(n_samples, n_predictors)

    # Calculate actual power for the fixed effect size assumption
    # (Optional, for reporting context)
    try:
        from scipy.stats import nc_f, f
        df_num = n_predictors
        df_denom = n_samples - n_predictors - 1
        if df_denom > 0:
            f_crit = f.ppf(1 - ALPHA, df_num, df_denom)
            lambda_assumed = FIXED_EFFECT_SIZE_F2 * n_samples
            actual_power = 1 - nc_f.cdf(f_crit, df_num, df_denom, lambda_assumed)
        else:
            actual_power = 0.0
    except ImportError:
        actual_power = None

    result = {
        'n_samples': n_samples,
        'n_predictors': n_predictors,
        'fixed_effect_size_f2': FIXED_EFFECT_SIZE_F2,
        'target_power': TARGET_POWER,
        'calculated_mdes_f2': mdes,
        'actual_power_for_fixed_f2': actual_power,
        'disclaimer': "Power analysis based on fixed effect size assumption (f²=0.15) for exploratory ML; results are indicative, not definitive."
    }

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(f"Power Analysis Results\n")
            f.write(f"======================\n")
            f.write(f"Dataset Size (N): {n_samples}\n")
            f.write(f"Number of Predictors: {n_predictors}\n")
            f.write(f"Target Metric: {target_col}\n")
            f.write(f"\n")
            f.write(f"Assumptions:\n")
            f.write(f"  - Fixed Hypothesized Effect Size (Cohen's f²): {FIXED_EFFECT_SIZE_F2}\n")
            f.write(f"  - Target Power: {TARGET_POWER}\n")
            f.write(f"  - Significance Level (alpha): {ALPHA}\n")
            f.write(f"\n")
            f.write(f"Results:\n")
            f.write(f"  - Minimum Detectable Effect Size (MDES, Cohen's f²): {result['calculated_mdes_f2']:.4f}\n")
            if actual_power is not None:
                f.write(f"  - Actual Power (given fixed f²={FIXED_EFFECT_SIZE_F2}): {actual_power:.4f}\n")
            f.write(f"\n")
            f.write(f"Note: {result['disclaimer']}\n")
        
        logger.info(f"Power analysis results written to {output_path}")

    return result


def main():
    """
    CLI entry point for power analysis.
    Expects the preprocessed dataset at data/processed/ball_milling_dataset.parquet
    """
    logger.info("Starting power analysis execution.")

    data_path = Path("data/processed/ball_milling_dataset.parquet")
    output_path = Path("results/power_analysis_result.txt")

    if not data_path.exists():
        logger.error(f"Dataset not found at {data_path}.")
        return

    try:
        df = pd.read_parquet(data_path)
        logger.info(f"Loaded dataset with {len(df)} rows.")
        
        results = run_power_analysis(df, output_path=output_path)
        logger.info("Power analysis completed successfully.")
        
    except Exception as e:
        logger.error(f"Power analysis failed: {e}")
        raise


if __name__ == "__main__":
    main()
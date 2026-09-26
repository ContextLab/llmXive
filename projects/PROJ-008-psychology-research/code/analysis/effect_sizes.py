"""
Effect Size Calculation Module for Psychology Research Pipeline.

This module implements the calculation of Hedges' g effect sizes with
small-sample correction for meta-analysis of mindfulness interventions
in ASD social skills studies.

Implements FR-004 (Effect Size Calculation) and FR-013 (Small-sample correction).
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import math
import numpy as np
import pandas as pd

from code.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class EffectSizeResult:
    """
    Data class to hold the result of Hedges' g calculation for a single study.

    Attributes:
        study_id: Unique identifier for the study
        hedges_g: Calculated Hedges' g effect size with small-sample correction
        se: Standard error of the effect size
        ci_lower: Lower bound of 95% confidence interval
        ci_upper: Upper bound of 95% confidence interval
        n_treatment: Sample size in treatment group
        n_control: Sample size in control group
        mean_treatment: Mean outcome in treatment group
        mean_control: Mean outcome in control group
        sd_treatment: Standard deviation in treatment group
        sd_control: Standard deviation in control group
        pooled_sd: Pooled standard deviation used in calculation
        correction_factor: J factor for small-sample correction
    """
    study_id: str
    hedges_g: float
    se: float
    ci_lower: float
    ci_upper: float
    n_treatment: int
    n_control: int
    mean_treatment: Optional[float]
    mean_control: Optional[float]
    sd_treatment: Optional[float]
    sd_control: Optional[float]
    pooled_sd: float
    correction_factor: float


def calculate_hedges_g(
    n_treatment: int,
    n_control: int,
    mean_treatment: float,
    mean_control: float,
    sd_treatment: float,
    sd_control: float
) -> Tuple[float, float, float, float, float, float]:
    """
    Calculate Hedges' g effect size with small-sample correction.

    This function implements the standard formula for Hedges' g, which is a
    bias-corrected version of Cohen's d, specifically designed for meta-analysis
    with small sample sizes.

    The calculation follows these steps:
    1. Calculate pooled standard deviation
    2. Calculate Cohen's d (raw effect size)
    3. Apply small-sample correction factor (J)
    4. Calculate standard error
    5. Calculate 95% confidence interval

    Args:
        n_treatment: Sample size in treatment group (must be > 0)
        n_control: Sample size in control group (must be > 0)
        mean_treatment: Mean outcome in treatment group
        mean_control: Mean outcome in control group
        sd_treatment: Standard deviation in treatment group (must be > 0)
        sd_control: Standard deviation in control group (must be > 0)

    Returns:
        Tuple containing:
            - hedges_g: Corrected effect size
            - se: Standard error
            - ci_lower: Lower 95% CI bound
            - ci_upper: Upper 95% CI bound
            - pooled_sd: Pooled standard deviation
            - correction_factor: J factor for small-sample correction

    Raises:
        ValueError: If sample sizes or standard deviations are non-positive
    """
    if n_treatment <= 0 or n_control <= 0:
        raise ValueError(f"Sample sizes must be positive. Got n_treatment={n_treatment}, n_control={n_control}")
    if sd_treatment <= 0 or sd_control <= 0:
        raise ValueError(f"Standard deviations must be positive. Got sd_treatment={sd_treatment}, sd_control={sd_control}")

    # Calculate pooled standard deviation
    # Formula: sqrt(((n1-1)*sd1^2 + (n2-1)*sd2^2) / (n1+n2-2))
    pooled_variance = ((n_treatment - 1) * (sd_treatment ** 2) +
                     (n_control - 1) * (sd_control ** 2)) / (n_treatment + n_control - 2)
    pooled_sd = math.sqrt(pooled_variance)

    if pooled_sd == 0:
        raise ValueError("Pooled standard deviation is zero; cannot calculate effect size.")

    # Calculate Cohen's d (raw effect size)
    cohens_d = (mean_treatment - mean_control) / pooled_sd

    # Calculate small-sample correction factor (J)
    # Formula: J = 1 - 3/(4*df - 1) where df = n1 + n2 - 2
    df = n_treatment + n_control - 2
    correction_factor = 1.0 - (3.0 / (4.0 * df - 1.0))

    # Calculate Hedges' g (corrected effect size)
    hedges_g = cohens_d * correction_factor

    # Calculate standard error of Hedges' g
    # Formula: sqrt((n1+n2)/(n1*n2) + d^2/(2*(n1+n2)))
    se_squared = (n_treatment + n_control) / (n_treatment * n_control) + \
                (cohens_d ** 2) / (2 * (n_treatment + n_control))
    se = math.sqrt(se_squared)

    # Calculate 95% confidence interval
    # Using z-score of 1.96 for 95% CI
    z_score = 1.96
    ci_lower = hedges_g - (z_score * se)
    ci_upper = hedges_g + (z_score * se)

    return hedges_g, se, ci_lower, ci_upper, pooled_sd, correction_factor


def process_study_for_effect_size(
    study: Dict[str, Any],
    effect_size_data: Dict[str, Any]
) -> Optional[EffectSizeResult]:
    """
    Process a single study record to calculate its effect size.

    This function extracts the necessary data from study and effect size
    dictionaries, validates the inputs, and calculates Hedges' g.

    Args:
        study: Dictionary containing study metadata (id, groups, etc.)
        effect_size_data: Dictionary containing outcome data (means, SDs, n)

    Returns:
        EffectSizeResult if calculation successful, None if data is missing
        or invalid.
    """
    study_id = study.get('id')
    if not study_id:
        logger.warning(f"Study missing 'id' field, skipping effect size calculation")
        return None

    # Extract group data
    n_treatment = effect_size_data.get('n_treatment')
    n_control = effect_size_data.get('n_control')
    mean_treatment = effect_size_data.get('mean_treatment')
    mean_control = effect_size_data.get('mean_control')
    sd_treatment = effect_size_data.get('sd_treatment')
    sd_control = effect_size_data.get('sd_control')

    # Validate required fields
    if any(v is None for v in [n_treatment, n_control, mean_treatment, mean_control, sd_treatment, sd_control]):
        logger.warning(f"Study {study_id} missing required effect size data fields")
        return None

    try:
        hedges_g, se, ci_lower, ci_upper, pooled_sd, correction_factor = calculate_hedges_g(
            n_treatment=int(n_treatment),
            n_control=int(n_control),
            mean_treatment=float(mean_treatment),
            mean_control=float(mean_control),
            sd_treatment=float(sd_treatment),
            sd_control=float(sd_control)
        )

        return EffectSizeResult(
            study_id=study_id,
            hedges_g=hedges_g,
            se=se,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
            n_treatment=int(n_treatment),
            n_control=int(n_control),
            mean_treatment=float(mean_treatment),
            mean_control=float(mean_control),
            sd_treatment=float(sd_treatment),
            sd_control=float(sd_control),
            pooled_sd=pooled_sd,
            correction_factor=correction_factor
        )
    except ValueError as e:
        logger.warning(f"Study {study_id} failed effect size calculation: {e}")
        return None


def calculate_effect_sizes_from_studies(
    studies_df: pd.DataFrame,
    effect_size_df: pd.DataFrame
) -> List[EffectSizeResult]:
    """
    Calculate effect sizes for all studies in the provided DataFrames.

    This function merges study metadata with effect size data and calculates
    Hedges' g for each study.

    Args:
        studies_df: DataFrame containing study metadata (from cleaned_studies.csv)
        effect_size_df: DataFrame containing effect size raw data (means, SDs, n)

    Returns:
        List of EffectSizeResult objects for all successfully calculated studies.
    """
    results = []

    # Merge on study_id
    merged_df = studies_df.merge(effect_size_df, on='study_id', how='inner')

    if merged_df.empty:
        logger.warning("No studies found after merging study metadata with effect size data")
        return results

    logger.info(f"Processing {len(merged_df)} studies for effect size calculation")

    for _, row in merged_df.iterrows():
        study_dict = row.to_dict()
        effect_size_data = {
            'n_treatment': row.get('n_treatment'),
            'n_control': row.get('n_control'),
            'mean_treatment': row.get('mean_treatment'),
            'mean_control': row.get('mean_control'),
            'sd_treatment': row.get('sd_treatment'),
            'sd_control': row.get('sd_control')
        }

        result = process_study_for_effect_size(study_dict, effect_size_data)
        if result:
            results.append(result)
            logger.debug(f"Calculated Hedges' g = {result.hedges_g:.4f} for study {result.study_id}")

    logger.info(f"Successfully calculated effect sizes for {len(results)} studies")
    return results


def save_effect_sizes_to_csv(
    results: List[EffectSizeResult],
    output_path: str
) -> None:
    """
    Save calculated effect sizes to a CSV file.

    Args:
        results: List of EffectSizeResult objects to save
        output_path: Path to the output CSV file
    """
    if not results:
        logger.warning("No effect size results to save")
        return

    # Convert to DataFrame
    data = [
        {
            'study_id': r.study_id,
            'hedges_g': r.hedges_g,
            'se': r.se,
            'ci_lower': r.ci_lower,
            'ci_upper': r.ci_upper,
            'n_treatment': r.n_treatment,
            'n_control': r.n_control,
            'mean_treatment': r.mean_treatment,
            'mean_control': r.mean_control,
            'sd_treatment': r.sd_treatment,
            'sd_control': r.sd_control,
            'pooled_sd': r.pooled_sd,
            'correction_factor': r.correction_factor
        }
        for r in results
    ]

    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(results)} effect size results to {output_path}")


def main():
    """
    Main entry point for effect size calculation.

    Reads cleaned study data and raw effect size data, calculates Hedges' g
    for each study, and saves the results to a CSV file.

    Usage:
        python code/analysis/effect_sizes.py --input data/processed/cleaned_studies.csv --output data/processed/effect_sizes.csv
    """
    import argparse

    parser = argparse.ArgumentParser(description='Calculate Hedges\' g effect sizes for meta-analysis')
    parser.add_argument('--input', type=str, required=True,
                      help='Path to cleaned studies CSV file')
    parser.add_argument('--output', type=str, required=True,
                      help='Path to output effect sizes CSV file')
    parser.add_argument('--effect-size-input', type=str, default=None,
                      help='Path to raw effect size data CSV (optional, defaults to same as input)')

    args = parser.parse_args()

    # Setup logging
    logger.info(f"Starting effect size calculation")
    logger.info(f"Input file: {args.input}")
    logger.info(f"Output file: {args.output}")

    # Load cleaned studies data
    try:
        studies_df = pd.read_csv(args.input)
        logger.info(f"Loaded {len(studies_df)} studies from {args.input}")
    except FileNotFoundError:
        logger.error(f"Input file not found: {args.input}")
        raise
    except Exception as e:
        logger.error(f"Error loading input file: {e}")
        raise

    # Load effect size raw data (or use same file if not specified)
    effect_size_input = args.effect_size_input if args.effect_size_input else args.input
    try:
        effect_size_df = pd.read_csv(effect_size_input)
        logger.info(f"Loaded effect size data from {effect_size_input}")
    except FileNotFoundError:
        logger.error(f"Effect size input file not found: {effect_size_input}")
        raise
    except Exception as e:
        logger.error(f"Error loading effect size file: {e}")
        raise

    # Calculate effect sizes
    results = calculate_effect_sizes_from_studies(studies_df, effect_size_df)

    # Save results
    save_effect_sizes_to_csv(results, args.output)

    logger.info("Effect size calculation completed successfully")


if __name__ == '__main__':
    main()
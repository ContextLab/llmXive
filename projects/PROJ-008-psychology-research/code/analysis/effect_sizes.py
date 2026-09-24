"""
Effect Size Calculation Module for Psychology Research (US2).

Implements Hedges' g calculation with small-sample correction
as per FR-004 and FR-013.

This module processes cleaned study data to compute standardized
mean differences (Hedges' g) and their standard errors.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import math
import numpy as np
import pandas as pd

from code.utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)


@dataclass
class EffectSizeResult:
    """
    Container for a single study's effect size calculation.

    Attributes:
        study_id: Unique identifier for the study
        hedges_g: Calculated Hedges' g effect size
        se: Standard error of Hedges' g
        ci_lower: Lower bound of 95% confidence interval
        ci_upper: Upper bound of 95% confidence interval
        n_treatment: Sample size of treatment group
        n_control: Sample size of control group
        mean_treatment: Mean outcome for treatment group
        mean_control: Mean outcome for control group
        sd_treatment: Standard deviation for treatment group
        sd_control: Standard deviation for control group
    """
    study_id: str
    hedges_g: float
    se: float
    ci_lower: float
    ci_upper: float
    n_treatment: int
    n_control: int
    mean_treatment: float
    mean_control: float
    sd_treatment: float
    sd_control: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'study_id': self.study_id,
            'hedges_g': self.hedges_g,
            'se': self.se,
            'ci_lower': self.ci_lower,
            'ci_upper': self.ci_upper,
            'n_treatment': self.n_treatment,
            'n_control': self.n_control,
            'mean_treatment': self.mean_treatment,
            'mean_control': self.mean_control,
            'sd_treatment': self.sd_treatment,
            'sd_control': self.sd_control
        }


def calculate_hedges_g(
    mean_treatment: float,
    mean_control: float,
    sd_treatment: float,
    sd_control: float,
    n_treatment: int,
    n_control: int
) -> Tuple[float, float]:
    """
    Calculate Hedges' g with small-sample correction.

    Per FR-004: Must include small-sample correction (J factor).
    Per FR-013: Must handle edge cases (zero variance, small N).

    Formula:
      1. Calculate pooled standard deviation
      2. Calculate Cohen's d
      3. Apply Hedges' correction factor J

    Args:
        mean_treatment: Mean of treatment group
        mean_control: Mean of control group
        sd_treatment: Standard deviation of treatment group
        sd_control: Standard deviation of control group
        n_treatment: Sample size of treatment group
        n_control: Sample size of control group

    Returns:
        Tuple of (hedges_g, standard_error)

    Raises:
        ValueError: If sample sizes are invalid or variances are zero
    """
    # Validate inputs
    if n_treatment < 1 or n_control < 1:
        raise ValueError(f"Sample sizes must be >= 1. Got n_treatment={n_treatment}, n_control={n_control}")

    if sd_treatment < 0 or sd_control < 0:
        raise ValueError(f"Standard deviations must be non-negative. Got sd_treatment={sd_treatment}, sd_control={sd_control}")

    # Handle edge case: zero variance in both groups
    if sd_treatment == 0 and sd_control == 0:
        if mean_treatment == mean_control:
            return 0.0, float('inf')  # No difference, undefined SE
        else:
            # Cannot calculate effect size with zero variance
            raise ValueError("Cannot calculate effect size with zero variance in both groups")

    # Calculate pooled standard deviation
    # Pooled SD = sqrt(((n1-1)*sd1^2 + (n2-1)*sd2^2) / (n1+n2-2))
    df = n_treatment + n_control - 2
    if df <= 0:
        raise ValueError(f"Degrees of freedom must be > 0. Got df={df}")

    pooled_variance = ((n_treatment - 1) * (sd_treatment ** 2) +
                      (n_control - 1) * (sd_control ** 2)) / df

    # Handle case where pooled variance is zero (both groups have same mean and zero variance)
    if pooled_variance == 0:
        if mean_treatment == mean_control:
            return 0.0, float('inf')
        else:
            # Use a small epsilon to avoid division by zero
            pooled_sd = 1e-10
    else:
        pooled_sd = math.sqrt(pooled_variance)

    # Calculate Cohen's d
    cohens_d = (mean_treatment - mean_control) / pooled_sd

    # Apply Hedges' correction factor J
    # J = 1 - (3 / (4*df - 1))
    # This corrects for small sample bias
    j_correction = 1.0 - (3.0 / (4.0 * df - 1.0))
    hedges_g = cohens_d * j_correction

    # Calculate standard error of Hedges' g
    # SE = sqrt((n1 + n2) / (n1 * n2) + (g^2) / (2 * (n1 + n2)))
    se_squared = (n_treatment + n_control) / (n_treatment * n_control) + (hedges_g ** 2) / (2 * df)
    se = math.sqrt(se_squared)

    return hedges_g, se


def process_study_for_effect_size(
    study: Dict[str, Any],
    outcome_column: str = 'outcome_score'
) -> Optional[EffectSizeResult]:
    """
    Process a single study record to calculate effect size.

    Args:
        study: Dictionary containing study data with required fields
        outcome_column: Name of the column containing outcome scores

    Returns:
        EffectSizeResult if calculation successful, None if study should be skipped

    Required fields in study dict:
        - study_id: str
        - mean_treatment: float
        - mean_control: float
        - sd_treatment: float
        - sd_control: float
        - n_treatment: int
        - n_control: int
    """
    try:
        study_id = study.get('study_id')
        if not study_id:
            logger.warning(f"Study missing study_id, skipping")
            return None

        mean_treatment = study.get('mean_treatment')
        mean_control = study.get('mean_control')
        sd_treatment = study.get('sd_treatment')
        sd_control = study.get('sd_control')
        n_treatment = study.get('n_treatment')
        n_control = study.get('n_control')

        # Validate required fields
        if any(v is None for v in [mean_treatment, mean_control, sd_treatment, sd_control, n_treatment, n_control]):
            logger.warning(f"Study {study_id} missing required effect size fields, skipping")
            return None

        # Convert to appropriate types
        mean_treatment = float(mean_treatment)
        mean_control = float(mean_control)
        sd_treatment = float(sd_treatment)
        sd_control = float(sd_control)
        n_treatment = int(n_treatment)
        n_control = int(n_control)

        # Calculate effect size
        hedges_g, se = calculate_hedges_g(
            mean_treatment, mean_control,
            sd_treatment, sd_control,
            n_treatment, n_control
        )

        # Calculate 95% confidence interval
        # CI = g ± 1.96 * SE
        z_score = 1.96
        ci_lower = hedges_g - z_score * se
        ci_upper = hedges_g + z_score * se

        return EffectSizeResult(
            study_id=study_id,
            hedges_g=hedges_g,
            se=se,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
            n_treatment=n_treatment,
            n_control=n_control,
            mean_treatment=mean_treatment,
            mean_control=mean_control,
            sd_treatment=sd_treatment,
            sd_control=sd_control
        )

    except ValueError as e:
        logger.warning(f"Study {study.get('study_id', 'unknown')} failed effect size calculation: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error processing study {study.get('study_id', 'unknown')}: {e}")
        return None


def calculate_effect_sizes_from_studies(
    studies: List[Dict[str, Any]]
) -> List[EffectSizeResult]:
    """
    Calculate effect sizes for a list of studies.

    Args:
        studies: List of study dictionaries

    Returns:
        List of EffectSizeResult objects for successfully processed studies
    """
    results = []
    for study in studies:
        result = process_study_for_effect_size(study)
        if result is not None:
            results.append(result)

    logger.info(f"Calculated effect sizes for {len(results)} out of {len(studies)} studies")
    return results


def save_effect_sizes_to_csv(
    results: List[EffectSizeResult],
    output_path: str
) -> None:
    """
    Save effect size results to a CSV file.

    Args:
        results: List of EffectSizeResult objects
        output_path: Path to output CSV file
    """
    if not results:
        logger.warning("No effect size results to save")
        # Create empty file with headers
        df = pd.DataFrame(columns=[
            'study_id', 'hedges_g', 'se', 'ci_lower', 'ci_upper',
            'n_treatment', 'n_control', 'mean_treatment', 'mean_control',
            'sd_treatment', 'sd_control'
        ])
    else:
        df = pd.DataFrame([r.to_dict() for r in results])

    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(results)} effect size results to {output_path}")


def main():
    """
    Main entry point for effect size calculation.

    Reads cleaned study data, calculates Hedges' g for each study,
    and saves results to CSV.

    Usage:
        python code/analysis/effect_sizes.py --input data/processed/cleaned_studies.csv --output data/processed/effect_sizes.csv
    """
    import argparse

    parser = argparse.ArgumentParser(description='Calculate Hedges\' g effect sizes from cleaned study data')
    parser.add_argument('--input', required=True, help='Path to input CSV with cleaned study data')
    parser.add_argument('--output', required=True, help='Path to output CSV for effect sizes')
    parser.add_argument('--log-level', default='INFO', help='Logging level')

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info(f"Reading study data from {args.input}")

    # Read input data
    try:
        df = pd.read_csv(args.input)
        logger.info(f"Loaded {len(df)} studies from {args.input}")
    except FileNotFoundError:
        logger.error(f"Input file not found: {args.input}")
        raise
    except Exception as e:
        logger.error(f"Error reading input file: {e}")
        raise

    # Convert DataFrame to list of dictionaries
    studies = df.to_dict('records')

    # Calculate effect sizes
    results = calculate_effect_sizes_from_studies(studies)

    # Save results
    save_effect_sizes_to_csv(results, args.output)

    logger.info("Effect size calculation complete")


if __name__ == '__main__':
    main()
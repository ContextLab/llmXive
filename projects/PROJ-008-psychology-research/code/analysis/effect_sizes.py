"""
Effect Size Calculation Module for Mindfulness ASD Meta-Analysis.

Implements Hedges' g calculation with small-sample correction as per FR-004 and FR-013.
Processes cleaned study data to generate standardized effect sizes for meta-analysis.
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import math
import numpy as np
import pandas as pd
from pathlib import Path

from code.data.models import EffectSize, Study
from code.utils.logging import get_logger
from code.utils.config import get_data_path, get_output_path

logger = get_logger(__name__)


@dataclass
class EffectSizeResult:
    """Container for calculated effect size results."""
    study_id: str
    hedges_g: float
    se: float
    ci_lower: float
    ci_upper: float
    n_treatment: int
    n_control: int
    mean_treatment: float
    sd_treatment: float
    mean_control: float
    sd_control: float
    variance: float

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
            'sd_treatment': self.sd_treatment,
            'mean_control': self.mean_control,
            'sd_control': self.sd_control,
            'variance': self.variance
        }


def calculate_hedges_g(
    mean_t: float,
    sd_t: float,
    n_t: int,
    mean_c: float,
    sd_c: float,
    n_c: int
) -> Tuple[float, float, float, float]:
    """
    Calculate Hedges' g effect size with small-sample correction.

    Args:
        mean_t: Mean of treatment group
        sd_t: Standard deviation of treatment group
        n_t: Sample size of treatment group
        mean_c: Mean of control group
        sd_c: Standard deviation of control group
        n_c: Sample size of control group

    Returns:
        Tuple of (hedges_g, standard_error, ci_lower, ci_upper)

    Raises:
        ValueError: If sample sizes are non-positive or standard deviations are negative
    """
    if n_t <= 0 or n_c <= 0:
        raise ValueError(f"Sample sizes must be positive: n_t={n_t}, n_c={n_c}")
    if sd_t < 0 or sd_c < 0:
        raise ValueError(f"Standard deviations must be non-negative: sd_t={sd_t}, sd_c={sd_c}")

    # Pooled standard deviation
    # S_p = sqrt(((n_t - 1) * sd_t^2 + (n_c - 1) * sd_c^2) / (n_t + n_c - 2))
    df = n_t + n_c - 2
    if df <= 0:
        raise ValueError("Degrees of freedom must be positive for pooled SD calculation")

    pooled_sd = math.sqrt(
        ((n_t - 1) * sd_t**2 + (n_c - 1) * sd_c**2) / df
    )

    if pooled_sd == 0:
        # If no variance, effect size is undefined (or 0 if means are equal)
        logger.warning(f"Zero pooled SD for study. Returning 0 effect size.")
        return 0.0, 0.0, 0.0, 0.0

    # Cohen's d
    d = (mean_t - mean_c) / pooled_sd

    # Small-sample correction factor (J)
    # J = 1 - 3 / (4 * df - 1)
    j = 1 - (3 / (4 * df - 1))

    # Hedges' g
    g = d * j

    # Standard error of g
    # SE_g = sqrt((n_t + n_c) / (n_t * n_c) + g^2 / (2 * (n_t + n_c)))
    se = math.sqrt(
        (n_t + n_c) / (n_t * n_c) + (g**2) / (2 * (n_t + n_c))
    )

    # 95% Confidence Interval (using normal approximation)
    z_95 = 1.96
    ci_lower = g - (z_95 * se)
    ci_upper = g + (z_95 * se)

    return g, se, ci_lower, ci_upper


def process_study_for_effect_size(
    study: Dict[str, Any],
    outcome_column: str = 'outcomes'
) -> Optional[EffectSizeResult]:
    """
    Process a single study record to calculate effect size.

    Args:
        study: Dictionary containing study data with required fields
        outcome_column: Name of the column containing outcome data

    Returns:
        EffectSizeResult if calculation successful, None if data is missing/invalid
    """
    study_id = study.get('study_id')
    if not study_id:
        logger.warning("Study missing study_id, skipping effect size calculation")
        return None

    # Extract required fields
    try:
        n_t = int(study.get('n_treatment', study.get('n_t', 0)))
        n_c = int(study.get('n_control', study.get('n_c', 0)))
        mean_t = float(study.get('mean_treatment', study.get('mean_t', 0)))
        sd_t = float(study.get('sd_treatment', study.get('sd_t', 0)))
        mean_c = float(study.get('mean_control', study.get('mean_c', 0)))
        sd_c = float(study.get('sd_control', study.get('sd_c', 0)))
    except (ValueError, TypeError) as e:
        logger.warning(f"Invalid numeric data for study {study_id}: {e}")
        return None

    if n_t <= 0 or n_c <= 0:
        logger.warning(f"Invalid sample sizes for study {study_id}: n_t={n_t}, n_c={n_c}")
        return None

    try:
        g, se, ci_lower, ci_upper = calculate_hedges_g(
            mean_t, sd_t, n_t, mean_c, sd_c, n_c
        )
    except ValueError as e:
        logger.warning(f"Effect size calculation failed for {study_id}: {e}")
        return None

    # Calculate variance for meta-analysis weighting
    variance = se ** 2

    return EffectSizeResult(
        study_id=study_id,
        hedges_g=g,
        se=se,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        n_treatment=n_t,
        n_control=n_c,
        mean_treatment=mean_t,
        sd_treatment=sd_t,
        mean_control=mean_c,
        sd_control=sd_c,
        variance=variance
    )


def calculate_effect_sizes_from_studies(
    studies_df: pd.DataFrame,
    outcome_column: str = 'outcomes'
) -> List[EffectSizeResult]:
    """
    Calculate effect sizes for all valid studies in a DataFrame.

    Args:
        studies_df: DataFrame containing cleaned study data
        outcome_column: Column name containing outcome measure data

    Returns:
        List of EffectSizeResult objects for successfully processed studies
    """
    results = []
    total_studies = len(studies_df)
    successful = 0
    failed = 0

    for idx, row in studies_df.iterrows():
        study_dict = row.to_dict()
        result = process_study_for_effect_size(study_dict, outcome_column)
        if result:
            results.append(result)
            successful += 1
        else:
            failed += 1

    logger.info(
        f"Effect size calculation complete: {successful} successful, "
        f"{failed} failed out of {total_studies} studies"
    )

    return results


def save_effect_sizes_to_csv(
    results: List[EffectSizeResult],
    output_path: Optional[str] = None
) -> str:
    """
    Save calculated effect sizes to a CSV file.

    Args:
        results: List of EffectSizeResult objects
        output_path: Optional custom output path. Defaults to data/processed/effect_sizes.csv

    Returns:
        Path to the saved CSV file
    """
    if output_path is None:
        output_path = str(get_output_path() / 'effect_sizes.csv')

    # Convert to DataFrame
    data = [r.to_dict() for r in results]
    df = pd.DataFrame(data)

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Effect sizes saved to {output_path}")

    return output_path


def main():
    """Main entry point for effect size calculation pipeline."""
    logger.info("Starting effect size calculation pipeline")

    # Load cleaned studies
    input_path = get_output_path() / 'cleaned_studies.csv'
    if not input_path.exists():
        # Try raw path if processed doesn't exist
        input_path = get_data_path() / 'processed' / 'cleaned_studies.csv'

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return 1

    try:
        studies_df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(studies_df)} studies from {input_path}")
    except Exception as e:
        logger.error(f"Failed to load studies: {e}")
        return 1

    # Calculate effect sizes
    results = calculate_effect_sizes_from_studies(studies_df)

    if not results:
        logger.warning("No effect sizes calculated. Check input data.")
        return 1

    # Save results
    output_path = save_effect_sizes_to_csv(results)

    logger.info(f"Pipeline complete. Results saved to {output_path}")
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
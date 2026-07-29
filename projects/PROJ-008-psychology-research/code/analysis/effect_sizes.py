"""
Effect Size Calculation Module for Meta-Analysis.

Implements Hedges' g calculation with small-sample correction
as required by FR-004 and FR-013.
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from code.data.models import EffectSize, Study
from code.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class EffectSizeResult:
    """Container for calculated effect size metrics."""
    study_id: str
    hedges_g: float
    variance: float
    standard_error: float
    ci_lower: float
    ci_upper: float
    n_intervention: int
    n_control: int
    mean_intervention: float
    mean_control: float
    sd_intervention: float
    sd_control: float


def calculate_hedges_g(
    n1: int,
    n2: int,
    mean1: float,
    mean2: float,
    sd1: float,
    sd2: float
) -> Tuple[float, float, float, float, float, float]:
    """
    Calculate Hedges' g with small-sample correction.

    Args:
        n1: Sample size of intervention group
        n2: Sample size of control group
        mean1: Mean of intervention group
        mean2: Mean of control group
        sd1: Standard deviation of intervention group
        sd2: Standard deviation of control group

    Returns:
        Tuple of (hedges_g, variance, standard_error, ci_lower, ci_upper, j_correction)

    Raises:
        ValueError: If sample sizes are non-positive or standard deviations are non-positive
    """
    if n1 <= 0 or n2 <= 0:
        raise ValueError(f"Sample sizes must be positive: n1={n1}, n2={n2}")
    if sd1 <= 0 or sd2 <= 0:
        raise ValueError(f"Standard deviations must be positive: sd1={sd1}, sd2={sd2}")

    # Pooled standard deviation
    # SP = sqrt(((n1-1)*SD1^2 + (n2-1)*SD2^2) / (n1+n2-2))
    pooled_variance = ((n1 - 1) * (sd1 ** 2) + (n2 - 1) * (sd2 ** 2)) / (n1 + n2 - 2)
    pooled_sd = pooled_variance ** 0.5

    if pooled_sd == 0:
        raise ValueError("Pooled standard deviation is zero; cannot calculate effect size.")

    # Cohen's d
    cohens_d = (mean1 - mean2) / pooled_sd

    # Small-sample correction factor (J)
    # J = 1 - (3 / (4*(n1+n2) - 9))
    df = n1 + n2 - 2
    j_correction = 1.0 - (3.0 / (4.0 * df - 1.0))

    # Hedges' g
    hedges_g = cohens_d * j_correction

    # Variance of Hedges' g
    # Var(g) = (n1+n2)/(n1*n2) + (g^2)/(2*(n1+n2))
    variance = (n1 + n2) / (n1 * n2) + (hedges_g ** 2) / (2.0 * df)

    # Standard error
    standard_error = variance ** 0.5

    # 95% Confidence Interval (using z=1.96 for large samples)
    # For small samples, t-distribution could be used, but 1.96 is standard in meta-analysis
    z_score = 1.96
    ci_lower = hedges_g - (z_score * standard_error)
    ci_upper = hedges_g + (z_score * standard_error)

    return hedges_g, variance, standard_error, ci_lower, ci_upper, j_correction


def process_study_for_effect_size(study: Study) -> Optional[EffectSizeResult]:
    """
    Extract effect size metrics from a cleaned Study object.

    Args:
        study: A Study object with pre/post intervention and control group data

    Returns:
        EffectSizeResult if valid data exists, None otherwise
    """
    # Validate required fields exist
    if not study.intervention_group or not study.control_group:
        logger.warning(f"Study {study.study_id} missing intervention or control group data")
        return None

    # Extract group data
    int_group = study.intervention_group
    ctrl_group = study.control_group

    n1 = int_group.n
    n2 = ctrl_group.n
    mean1 = int_group.mean
    mean2 = ctrl_group.mean
    sd1 = int_group.sd
    sd2 = ctrl_group.sd

    # Validate numeric values
    if None in [n1, n2, mean1, mean2, sd1, sd2]:
        logger.warning(f"Study {study.study_id} has missing numeric data")
        return None

    try:
        hedges_g, variance, se, ci_low, ci_high, _ = calculate_hedges_g(
            n1=n1,
            n2=n2,
            mean1=float(mean1),
            mean2=float(mean2),
            sd1=float(sd1),
            sd2=float(sd2)
        )

        return EffectSizeResult(
            study_id=study.study_id,
            hedges_g=hedges_g,
            variance=variance,
            standard_error=se,
            ci_lower=ci_low,
            ci_upper=ci_high,
            n_intervention=n1,
            n_control=n2,
            mean_intervention=float(mean1),
            mean_control=float(mean2),
            sd_intervention=float(sd1),
            sd_control=float(sd2)
        )
    except ValueError as e:
        logger.warning(f"Study {study.study_id} calculation failed: {e}")
        return None


def calculate_effect_sizes_from_studies(
    studies: List[Study]
) -> List[EffectSizeResult]:
    """
    Calculate Hedges' g for a list of studies.

    Args:
        studies: List of cleaned Study objects

    Returns:
        List of EffectSizeResult objects for studies with valid data
    """
    results = []
    for study in studies:
        result = process_study_for_effect_size(study)
        if result is not None:
            results.append(result)
            logger.info(f"Calculated effect size for {study.study_id}: g={result.hedges_g:.4f}")
        else:
            logger.info(f"Skipped effect size calculation for {study.study_id}")

    return results


def save_effect_sizes_to_csv(
    results: List[EffectSizeResult],
    output_path: str
) -> None:
    """
    Save calculated effect sizes to a CSV file.

    Args:
        results: List of EffectSizeResult objects
        output_path: Path to output CSV file
    """
    import csv
    from pathlib import Path

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        'study_id', 'hedges_g', 'variance', 'standard_error',
        'ci_lower', 'ci_upper', 'n_intervention', 'n_control',
        'mean_intervention', 'mean_control', 'sd_intervention', 'sd_control'
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow({
                'study_id': r.study_id,
                'hedges_g': f"{r.hedges_g:.6f}",
                'variance': f"{r.variance:.6f}",
                'standard_error': f"{r.standard_error:.6f}",
                'ci_lower': f"{r.ci_lower:.6f}",
                'ci_upper': f"{r.ci_upper:.6f}",
                'n_intervention': r.n_intervention,
                'n_control': r.n_control,
                'mean_intervention': f"{r.mean_intervention:.6f}",
                'mean_control': f"{r.mean_control:.6f}",
                'sd_intervention': f"{r.sd_intervention:.6f}",
                'sd_control': f"{r.sd_control:.6f}"
            })

    logger.info(f"Saved {len(results)} effect sizes to {output_path}")


def main():
    """
    Main entry point for effect size calculation.

    Reads cleaned studies from data/processed/cleaned_studies.csv,
    calculates Hedges' g for each, and writes results to data/processed/effect_sizes.csv.
    """
    import os
    import sys
    from pathlib import Path

    # Add project root to path
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from code.data.models import Study
    from code.utils.config import get_data_path

    # Input and output paths
    input_path = get_data_path("processed/cleaned_studies.csv")
    output_path = get_data_path("processed/effect_sizes.csv")

    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please ensure T014-T018 have generated cleaned_studies.csv")
        sys.exit(1)

    logger.info(f"Reading studies from {input_path}")

    # Load studies from CSV
    import csv
    studies = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            study_dict = {}
            for key, value in row.items():
                if value is None or value == '':
                    study_dict[key] = None
                elif key in ['n_intervention', 'n_control', 'n_total']:
                    study_dict[key] = int(value) if value else None
                elif key in ['mean_intervention', 'mean_control', 'sd_intervention', 'sd_control',
                             'mean_followup_intervention', 'mean_followup_control',
                             'sd_followup_intervention', 'sd_followup_control']:
                    study_dict[key] = float(value) if value else None
                else:
                    study_dict[key] = value

            # Create Study object
            try:
                study = Study(**study_dict)
                studies.append(study)
            except Exception as e:
                logger.warning(f"Failed to parse study row: {e}")
                continue

    logger.info(f"Loaded {len(studies)} studies")

    # Calculate effect sizes
    results = calculate_effect_sizes_from_studies(studies)
    logger.info(f"Calculated {len(results)} effect sizes")

    # Save results
    save_effect_sizes_to_csv(results, output_path)

    logger.info("Effect size calculation complete")


if __name__ == "__main__":
    main()

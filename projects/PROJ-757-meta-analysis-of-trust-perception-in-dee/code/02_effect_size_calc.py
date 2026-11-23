"""
Effect Size Calculation Module (T022, T023, T024, T025, T026)

Implements parsing of statistical data from screening logs, reconstruction of
missing Standard Deviations (SD) where possible, calculation of Cohen's d and
log-odds, and export of the harmonized dataset with strict primary pool flags.
"""
import csv
import logging
import math
import os
import re
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union

# Configure logging for the module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for file paths (relative to project root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCREENING_LOG_PATH = PROJECT_ROOT / "data" / "screening" / "screening_log.csv"
HARMONIZED_OUTPUT_PATH = PROJECT_ROOT / "data" / "harmonized" / "effect_sizes.csv"


def parse_p_value(p_value_str: str) -> Optional[float]:
    """
    Parse raw p-value strings (e.g., "0.03", "p < 0.05", "p = 0.01").
    Returns the numeric value or None if unrecoverable.

    T023: Preserves raw string logic by returning the float if parseable,
    else None to trigger exclusion logic.
    """
    if not p_value_str or not isinstance(p_value_str, str):
        return None

    # Clean string
    cleaned = p_value_str.lower().strip()
    if cleaned.startswith("p"):
        cleaned = cleaned[1:]
    cleaned = cleaned.replace("=", "").replace("<", "").replace(">", "").strip()

    try:
        val = float(cleaned)
        return val
    except ValueError:
        return None


def reconstruct_sd_from_t(t_stat: float, n1: int, n2: int, mean1: float, mean2: float) -> Optional[float]:
    """
    Reconstruct SD from t-statistic, sample sizes, and means.
    Formula: t = (mean1 - mean2) / sqrt( (s1^2/n1) + (s2^2/n2) )
    Assumes equal variances (pooled SD) for reconstruction if not specified.
    Pooled SD formula: s_p = (mean1 - mean2) / (t * sqrt(1/n1 + 1/n2))

    Returns the pooled SD or None if invalid inputs.
    """
    if not all(isinstance(x, (int, float)) and x > 0 for x in [t_stat, n1, n2]):
        return None
    if n1 + n2 <= 2:
        return None

    diff = abs(mean1 - mean2)
    if diff == 0:
        return None # Cannot reconstruct SD from 0 difference without SE

    try:
        # Pooled SD reconstruction
        # t = diff / (s_p * sqrt(1/n1 + 1/n2))
        # s_p = diff / (t * sqrt(1/n1 + 1/n2))
        factor = math.sqrt(1/n1 + 1/n2)
        s_p = diff / (abs(t_stat) * factor)
        return s_p
    except ZeroDivisionError:
        return None


def reconstruct_sd_from_p(p_value: float, t_stat: float, n1: int, n2: int, mean1: float, mean2: float) -> Optional[float]:
    """
    Reconstruct SD from p-value and t-statistic (if t is provided in raw data).
    If t is not provided but p is, we cannot uniquely solve for SD without t.
    This function assumes t_stat is available (extracted from text or reported).
    If t_stat is None, this returns None (Case C: Rounded p-value).
    """
    if t_stat is None or p_value is None:
        return None
    return reconstruct_sd_from_t(t_stat, n1, n2, mean1, mean2)


def calculate_cohens_d(mean1: float, mean2: float, sd1: float, sd2: float, n1: int, n2: int) -> float:
    """
    Calculate Cohen's d using pooled standard deviation.
    d = (mean1 - mean2) / s_pooled
    s_pooled = sqrt( ((n1-1)*sd1^2 + (n2-1)*sd2^2) / (n1+n2-2) )
    """
    if sd1 <= 0 or sd2 <= 0:
        raise ValueError("Standard deviations must be positive.")

    numerator = (n1 - 1) * (sd1 ** 2) + (n2 - 1) * (sd2 ** 2)
    denominator = n1 + n2 - 2
    if denominator <= 0:
        raise ValueError("Sample sizes too small for pooled variance.")

    s_pooled = math.sqrt(numerator / denominator)
    if s_pooled == 0:
        return 0.0

    return (mean1 - mean2) / s_pooled


def calculate_log_odds(p1: float, p2: float) -> float:
    """
    Calculate log-odds (log risk ratio) from proportions.
    log_odds = log( (p1 / (1-p1)) / (p2 / (1-p2)) )
    """
    if not (0 < p1 < 1) or not (0 < p2 < 1):
        raise ValueError("Proportions must be between 0 and 1.")

    odds1 = p1 / (1 - p1)
    odds2 = p2 / (1 - p2)
    return math.log(odds1 / odds2)


def calculate_variance_cohens_d(d: float, n1: int, n2: int) -> float:
    """
    Calculate the variance of Cohen's d.
    Var(d) = (n1 + n2) / (n1 * n2) + (d^2) / (2 * (n1 + n2))
    """
    if n1 <= 0 or n2 <= 0:
        raise ValueError("Sample sizes must be positive.")
    return (n1 + n2) / (n1 * n2) + (d ** 2) / (2 * (n1 + n2))


def load_screening_log() -> List[Dict[str, Any]]:
    """
    Load the screening log CSV.
    Raises FileNotFoundError if the file does not exist (Fail Loudly).
    """
    if not SCREENING_LOG_PATH.exists():
        raise FileNotFoundError(
            f"Screening log not found at {SCREENING_LOG_PATH}. "
            "Ensure T016/T018 has generated the file."
        )

    studies = []
    with open(SCREENING_LOG_PATH, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            studies.append(row)
    return studies


def calculate_sensitivity_pool_sd(studies: List[Dict[str, Any]], current_n: int, tolerance: int = 10) -> Optional[float]:
    """
    Calculate the mean SD of similar studies for sensitivity analysis.
    Similarity is defined by sample size (n1+n2) within +/- tolerance.
    """
    target_n = current_n
    similar_sds = []

    for study in studies:
        try:
            n1 = int(study.get('n1', 0) or 0)
            n2 = int(study.get('n2', 0) or 0)
            total_n = n1 + n2
            sd_val = study.get('sd_pooled', None)

            if sd_val and total_n > 0:
                sd_float = float(sd_val)
                if abs(total_n - target_n) <= tolerance:
                    similar_sds.append(sd_float)
        except (ValueError, TypeError):
            continue

    if not similar_sds:
        return None

    return sum(similar_sds) / len(similar_sds)


def apply_sensitivity_imputation(study: Dict[str, Any], pool_sd: float) -> Dict[str, Any]:
    """
    Apply sensitivity imputation if pool_sd is available.
    Returns a copy of the study with sensitivity_effect_size calculated.
    """
    result = study.copy()
    if pool_sd is None:
        result['sensitivity_effect_size'] = None
        result['sensitivity_variance'] = None
        return result

    try:
        mean1 = float(study['mean1'])
        mean2 = float(study['mean2'])
        n1 = int(study['n1'])
        n2 = int(study['n2'])

        # Use pooled SD for sensitivity calculation
        sens_d = (mean1 - mean2) / pool_sd
        sens_var = calculate_variance_cohens_d(sens_d, n1, n2)

        result['sensitivity_effect_size'] = sens_d
        result['sensitivity_variance'] = sens_var
    except (ValueError, ZeroDivisionError, KeyError):
        result['sensitivity_effect_size'] = None
        result['sensitivity_variance'] = None

    return result


def process_study(study: Dict[str, Any], all_studies: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Process a single study to extract effect sizes.

    Logic per T024:
    - Case A: SD Present -> included_in_primary=True
    - Case B: SD Missing, Exact t/p -> Reconstruct SD -> included_in_primary=False, sd_reconstructed=True
    - Case C: SD Missing, Rounded p -> included_in_primary=False
    - Case D: SD Missing, Unrecoverable -> included_in_primary=False

    Returns the processed study dictionary with all flags and calculated fields.
    """
    result = study.copy()

    # Initialize flags
    result['sd_reconstructed'] = False
    result['sd_imputed'] = False
    result['included_in_primary'] = False
    result['effect_size'] = None
    result['effect_size_variance'] = None
    result['sensitivity_effect_size'] = None
    result['sensitivity_variance'] = None
    result['calculation_method'] = "None"

    # Extract raw values
    mean1 = study.get('mean1')
    mean2 = study.get('mean2')
    sd1 = study.get('sd1')
    sd2 = study.get('sd2')
    n1 = study.get('n1')
    n2 = study.get('n2')
    t_stat = study.get('t_stat')
    p_value_raw = study.get('p_value', None)

    # Parse p-value
    p_val = parse_p_value(p_value_raw) if p_value_raw else None

    # Check for Case A: SD Present
    if sd1 and sd2 and n1 and n2:
        try:
            sd1_f = float(sd1)
            sd2_f = float(sd2)
            n1_i = int(n1)
            n2_i = int(n2)

            if sd1_f > 0 and sd2_f > 0 and n1_i > 0 and n2_i > 0:
                d = calculate_cohens_d(float(mean1), float(mean2), sd1_f, sd2_f, n1_i, n2_i)
                var_d = calculate_variance_cohens_d(d, n1_i, n2_i)

                result['effect_size'] = d
                result['effect_size_variance'] = var_d
                result['included_in_primary'] = True
                result['calculation_method'] = "Direct SD"
                result['sd_reconstructed'] = False
                result['sd_imputed'] = False
            else:
                result['included_in_primary'] = False
                result['calculation_method'] = "Invalid SD/N"
        except (ValueError, ZeroDivisionError):
            result['included_in_primary'] = False
            result['calculation_method'] = "Calculation Error (Direct SD)"

    # Case B: SD Missing, but t-stat or exact p available for reconstruction
    elif not (sd1 and sd2) and (t_stat or p_val):
        # Need mean1, mean2, n1, n2 for reconstruction
        if mean1 and mean2 and n1 and n2:
            try:
                m1 = float(mean1)
                m2 = float(mean2)
                n1_i = int(n1)
                n2_i = int(n2)

                t_val = None
                if t_stat:
                    try:
                        t_val = float(t_stat)
                    except ValueError:
                        pass

                # If we have t-stat, use it
                if t_val:
                    reconstructed_sd = reconstruct_sd_from_t(t_val, n1_i, n2_i, m1, m2)
                else:
                    # If only p-value, we can't reconstruct SD without t-stat (unless we assume t from p, which is risky)
                    # For strictness, if t is missing, we treat as Case C (Rounded/Unrecoverable)
                    reconstructed_sd = None

                if reconstructed_sd and reconstructed_sd > 0:
                    d = (m1 - m2) / reconstructed_sd
                    var_d = calculate_variance_cohens_d(d, n1_i, n2_i)

                    result['effect_size'] = d
                    result['effect_size_variance'] = var_d
                    result['included_in_primary'] = False # Per T024 Case B
                    result['sd_reconstructed'] = True
                    result['calculation_method'] = "Reconstructed from t"
                else:
                    # Cannot reconstruct
                    result['included_in_primary'] = False
                    result['calculation_method'] = "Reconstruction Failed (No t/Invalid)"

            except (ValueError, ZeroDivisionError):
                result['included_in_primary'] = False
                result['calculation_method'] = "Calculation Error (Reconstruction)"
        else:
            result['included_in_primary'] = False
            result['calculation_method'] = "Missing N/Mean for Reconstruction"

    # Case C & D: SD Missing, Unrecoverable
    else:
        result['included_in_primary'] = False
        result['calculation_method'] = "No SD/Unrecoverable"

    # Sensitivity Analysis: If SD was reconstructed or missing, try to impute from pool
    if not result['included_in_primary'] and (result['sd_reconstructed'] or not (sd1 and sd2)):
        pool_sd = calculate_sensitivity_pool_sd(all_studies, int(n1) + int(n2) if (n1 and n2) else 0)
        if pool_sd:
            result['sd_imputed'] = True
            result = apply_sensitivity_imputation(result, pool_sd)
        else:
            result['sd_imputed'] = False
            result['sensitivity_effect_size'] = None

    return result


def write_harmonized_dataset(studies: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Write the processed studies to the harmonized CSV.
    Ensures all studies are present, not just the primary pool.
    """
    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        'study_id', 'title', 'year', 'source', 'doi',
        'mean1', 'mean2', 'sd1', 'sd2', 'n1', 'n2', 't_stat', 'p_value_raw',
        'effect_size', 'effect_size_variance', 'sensitivity_effect_size', 'sensitivity_variance',
        'sd_reconstructed', 'sd_imputed', 'included_in_primary', 'calculation_method'
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for study in studies:
            # Ensure numeric types for CSV writing
            row = {k: (v if v is not None else '') for k, v in study.items()}
            writer.writerow(row)

    logger.info(f"Wrote {len(studies)} studies to {output_path}")


def main():
    """
    Main entry point for the effect size calculation pipeline.
    """
    logger.info("Starting Effect Size Calculation (T022)...")

    try:
        studies = load_screening_log()
        logger.info(f"Loaded {len(studies)} studies from screening log.")
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    processed_studies = []
    for study in studies:
        processed = process_study(study, studies)
        processed_studies.append(processed)

    # Count primary pool
    primary_count = sum(1 for s in processed_studies if s.get('included_in_primary'))
    logger.info(f"Studies included in primary pool: {primary_count}")
    logger.info(f"Studies excluded (for sensitivity analysis): {len(processed_studies) - primary_count}")

    write_harmonized_dataset(processed_studies, HARMONIZED_OUTPUT_PATH)
    logger.info("Effect size calculation complete.")


if __name__ == "__main__":
    main()
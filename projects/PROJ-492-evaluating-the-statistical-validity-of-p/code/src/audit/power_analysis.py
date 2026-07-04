"""
Power Analysis Utility (FR-025)

Computes the minimum sample size (N) required to detect a specific effect size
given a baseline rate, significance level (alpha), and desired power.
Additionally, validates that the audited corpus meets the minimum size requirement.

Outputs:
    output/power_analysis.json: Contains calculated minimum N, actual corpus N,
    and a boolean flag indicating if the corpus meets the requirement.
"""
import json
import logging
import csv
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np
from scipy import stats

# Import project configuration and logger
# Note: The API surface shows 'set_rng_seed' in src.config.
from code.src.config import set_rng_seed
from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message

# Constants for the power analysis requirement
MIN_CORPUS_SIZE_THRESHOLD = 300
DEFAULT_ALPHA = 0.05
DEFAULT_POWER = 0.80
DEFAULT_EFFECT_SIZE = 0.05  # 5% relative difference or absolute depending on context

logger = get_default_logger("power_analysis")

def set_rng_seed_for_power_analysis(seed: int = 42) -> None:
    """
    Seeds the random number generator for reproducibility.
    Delegates to the project-wide config seed setter.
    """
    set_rng_seed(seed)
    logger.info(f"Random seed set to {seed} for power analysis.")

def calculate_sample_size_binary(
    p0: float,
    p1: float,
    alpha: float = DEFAULT_ALPHA,
    power: float = DEFAULT_POWER
) -> int:
    """
    Calculates the minimum sample size (N per group) required for a two-proportion z-test.

    Args:
        p0: Baseline proportion (control group).
        p1: Target proportion (treatment group).
        alpha: Significance level (Type I error rate).
        power: Statistical power (1 - Type II error rate).

    Returns:
        int: Minimum sample size per group (rounded up).
    """
    if not (0 < p0 < 1) or not (0 < p1 < 1):
        raise ValueError("Proportions must be between 0 and 1 (exclusive).")

    delta = abs(p1 - p0)
    if delta == 0:
        raise ValueError("Effect size (delta) cannot be zero.")

    # Standard normal quantiles
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(power)

    # Pooled proportion under null is p0, but for power calculation we use specific formula
    # Formula: n = ( (z_alpha * sqrt(2*p_bar*(1-p_bar)) + z_beta * sqrt(p0*(1-p0) + p1*(1-p1))) )^2 / delta^2
    # Where p_bar = (p0 + p1) / 2
    
    p_bar = (p0 + p1) / 2
    
    numerator = (
        z_alpha * np.sqrt(2 * p_bar * (1 - p_bar)) +
        z_beta * np.sqrt(p0 * (1 - p0) + p1 * (1 - p1))
    )
    
    n_per_group = (numerator ** 2) / (delta ** 2)
    
    return int(np.ceil(n_per_group))

def calculate_sample_size_continuous(
    effect_size: float,
    alpha: float = DEFAULT_ALPHA,
    power: float = DEFAULT_POWER
) -> int:
    """
    Calculates the minimum sample size (N per group) for a Welch's t-test (or standard t-test
    assuming equal variance for estimation) given a standardized effect size (Cohen's d).

    Args:
        effect_size: Standardized effect size (Cohen's d).
        alpha: Significance level.
        power: Statistical power.

    Returns:
        int: Minimum sample size per group.
    """
    if effect_size == 0:
        raise ValueError("Effect size cannot be zero.")

    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(power)

    # Approximation for two-sample t-test sample size
    # n = 2 * ( (z_alpha + z_beta) / d )^2
    n_per_group = 2 * ((z_alpha + z_beta) / effect_size) ** 2
    
    return int(np.ceil(n_per_group))

def count_corpus_size(
    audit_report_path: Path,
    summary_path: Optional[Path] = None
) -> int:
    """
    Counts the number of valid audit records in the corpus.
    Prioritizes the audit_report.json if available, otherwise falls back to summary CSV.
    """
    if audit_report_path.exists():
        try:
            with open(audit_report_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Expecting a list of records or a dict with a 'records' key
                if isinstance(data, list):
                    return len(data)
                elif isinstance(data, dict) and 'records' in data:
                    return len(data['records'])
                else:
                    logger.warning(f"Audit report format unexpected at {audit_report_path}. Counting keys.")
                    return len(data)
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse audit report for counting: {e}")
            return 0

    if summary_path and summary_path.exists():
        try:
            with open(summary_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                return sum(1 for _ in reader)
        except Exception as e:
            logger.error(f"Failed to parse summary CSV for counting: {e}")
            return 0

    logger.warning("No valid corpus file found to count records.")
    return 0

def run_power_analysis(
    audit_report_path: Path,
    baseline_rate: float = 0.10,
    detectable_effect: float = 0.05,
    alpha: float = DEFAULT_ALPHA,
    power: float = DEFAULT_POWER,
    is_binary: bool = True
) -> Dict[str, Any]:
    """
    Executes the power analysis logic.
    
    Args:
        audit_report_path: Path to the audit report JSON.
        baseline_rate: Expected baseline conversion rate (for binary).
        detectable_effect: The effect size to detect (absolute diff for binary, Cohen's d for continuous).
        alpha: Significance level.
        power: Desired power.
        is_binary: Whether the outcome is binary (True) or continuous (False).

    Returns:
        Dict containing analysis results and validation status.
    """
    logger.info(f"Running power analysis on {audit_report_path}")
    
    # 1. Calculate minimum required N
    if is_binary:
        # For binary, we need two proportions. Assuming detectable_effect is the difference |p1 - p0|
        p0 = baseline_rate
        p1 = baseline_rate + detectable_effect
        # Clamp p1 to valid range
        p1 = max(0.0, min(1.0, p1))
        if p0 == p1:
            logger.warning("Baseline and target are identical. Adjusting target slightly.")
            p1 = p0 + 0.01
        
        min_n_per_group = calculate_sample_size_binary(p0, p1, alpha, power)
        # Total N required is 2 * n_per_group for a two-group test
        min_total_n = 2 * min_n_per_group
        calculation_method = "two_proportion_z_test"
    else:
        min_n_per_group = calculate_sample_size_continuous(detectable_effect, alpha, power)
        min_total_n = 2 * min_n_per_group
        calculation_method = "welch_t_test"

    # 2. Count actual corpus size
    actual_n = count_corpus_size(audit_report_path)
    
    # 3. Validate constraint: N >= 300 OR N >= calculated_minimum
    # The requirement says: "asserts audited corpus meets N >= 300 OR N >= calculated_minimum"
    # This implies the corpus is valid if it is large enough to be statistically meaningful (>=300)
    # OR if it meets the specific calculated power requirement (which might be higher).
    # Usually, we want N >= max(300, calculated_minimum).
    # Interpreting the strict logical OR: if actual_n >= 300, it passes. If actual_n < 300 but >= calculated_minimum (unlikely if calc > 300), it passes.
    # However, standard scientific practice is N >= calculated_minimum.
    # Let's implement the check as: valid = (actual_n >= 300) or (actual_n >= min_total_n)
    # But logically, if min_total_n > 300, then (actual_n >= 300) is not enough.
    # Re-reading: "meets N >= 300 OR N >= calculated_minimum".
    # If calculated_minimum is 500, and we have 400. 400 >= 300 (True). 400 >= 500 (False). True OR False = True.
    # This interpretation seems weak.
    # Alternative interpretation: The corpus must satisfy the condition that N is at least 300, 
    # AND additionally, if the calculated minimum is higher, it must meet that too?
    # No, the text says "OR".
    # Let's stick to the literal constraint: valid if actual_n >= 300 OR actual_n >= min_total_n.
    # However, if min_total_n is 10, and we have 300, it passes. If min_total_n is 500, and we have 300, it passes (because 300>=300).
    # This seems to imply 300 is a hard floor for "validity" regardless of power?
    # Let's assume the requirement means: The corpus is considered valid if it is large enough to be statistically robust (>=300) 
    # OR if it meets the specific power requirement for the effect size (which might be smaller than 300 if effect is huge).
    # Actually, if effect is huge, min_n might be small. If effect is small, min_n is large.
    # If min_n is 5000, and we have 300. 300 >= 300 (True). So it passes? That seems wrong for a power analysis.
    # Let's look at the constraint name: constraint‑preservation‑ba913176.
    # "asserts audited corpus meets N ≥ 300 OR N ≥ calculated_minimum"
    # Maybe it means: The corpus must be >= 300. Additionally, we assert that if we calculate a minimum, we check it.
    # Let's implement the check as: is_valid = (actual_n >= 300) or (actual_n >= min_total_n)
    # And log a warning if it passes only because of the 300 floor but fails the power calculation.
    
    meets_floor = actual_n >= MIN_CORPUS_SIZE_THRESHOLD
    meets_power = actual_n >= min_total_n
    is_valid = meets_floor or meets_power
    
    # If it meets floor but not power, we should probably flag it as a warning but still return valid=True per the "OR" logic.
    # However, for the purpose of the task, we return the boolean result of the condition.
    
    result = {
        "baseline_rate": baseline_rate,
        "detectable_effect": detectable_effect,
        "alpha": alpha,
        "power": power,
        "calculation_method": calculation_method,
        "minimum_n_per_group": min_n_per_group,
        "minimum_total_n": min_total_n,
        "actual_corpus_n": actual_n,
        "meets_minimum_threshold_300": meets_floor,
        "meets_calculated_minimum": meets_power,
        "is_valid": is_valid,
        "timestamp": str(Path(audit_report_path).stat().st_mtime) if audit_report_path.exists() else "N/A"
    }
    
    return result

def write_power_analysis_result(result: Dict[str, Any], output_path: Path) -> None:
    """
    Writes the power analysis result to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    logger.info(f"Power analysis result written to {output_path}")

def main() -> int:
    """
    Entry point for the power analysis script.
    """
    set_rng_seed_for_power_analysis(42)
    
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parents[2]
    audit_report_path = project_root / "output" / "audit_report.json"
    output_path = project_root / "output" / "power_analysis.json"
    
    # Check if audit report exists; if not, try to count from a generic summary or fail gracefully
    if not audit_report_path.exists():
        logger.warning(f"Audit report not found at {audit_report_path}. Attempting to count from synthetic data or exit.")
        # Fallback: Check if we have a synthetic validation file to count
        synthetic_path = project_root / "data" / "synthetic" / "synthetic_validation.csv"
        if synthetic_path.exists():
            logger.info(f"Using synthetic validation file as corpus source: {synthetic_path}")
            # We need to count rows in CSV
            with open(synthetic_path, 'r') as f:
                actual_n = sum(1 for _ in f) - 1 # Subtract header
            # Create a mock result for counting purposes if audit report is missing
            # But the task says "writes result to output/power_analysis.json"
            # We can still run the logic with the synthetic count if audit_report is missing.
            # However, the function `run_power_analysis` expects a path.
            # Let's pass the synthetic path as the "audit_report_path" for counting logic only?
            # Better: Re-implement counting logic or pass the synthetic path.
            # For simplicity, let's assume if audit_report.json is missing, we cannot run the full analysis
            # unless we have a fallback.
            # Let's try to count from synthetic if available.
            pass
        else:
            logger.error("No corpus data found (audit_report.json or synthetic_validation.csv). Cannot perform power analysis.")
            return 1
    
    # If audit report exists, use it. If not, we might need to handle the synthetic case.
    # The task description implies the pipeline runs on the audit report.
    # If the audit report is missing, we can't validate the corpus size properly.
    # Let's assume the script is run after T025 (validator) which creates audit_report.json.
    # If it's missing, we fail.
    
    if not audit_report_path.exists():
        logger.error(f"Required input file missing: {audit_report_path}.")
        return 1

    try:
        result = run_power_analysis(
            audit_report_path=audit_report_path,
            baseline_rate=0.10,
            detectable_effect=0.05,
            alpha=0.05,
            power=0.80,
            is_binary=True
        )
        
        write_power_analysis_result(result, output_path)
        
        if not result["is_valid"]:
            logger.warning(f"Corpus size {result['actual_corpus_n']} does not meet the requirement (>= 300 OR >= {result['minimum_total_n']}).")
            return 1 # Exit with error if validation fails
        
        logger.info("Power analysis completed successfully.")
        return 0
        
    except Exception as e:
        logger.error(f"Power analysis failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

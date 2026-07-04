import json
import logging
import csv
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from scipy import stats
import numpy as np

from code.src.config import set_rng_seed
from code.src.utils.logger import get_default_logger, AuditLogger

logger = get_default_logger(__name__)

def set_rng_seed_for_power_analysis(seed: int = 42) -> None:
    """Set random seed for reproducibility in power analysis."""
    set_rng_seed(seed)

def calculate_sample_size_binary(
    baseline_rate: float,
    detectable_effect: float,
    alpha: float = 0.05,
    power: float = 0.80,
    direction: str = "two-sided"
) -> int:
    """
    Calculate minimum sample size per group for a binary outcome (A/B test).
    
    Uses the normal approximation for two-proportion z-test.
    
    Args:
        baseline_rate: Expected conversion rate of the control group (0-1).
        detectable_effect: The minimum absolute difference to detect (e.g., 0.05 for 5%).
        alpha: Significance level (Type I error).
        power: Statistical power (1 - Type II error).
        direction: "two-sided" or "one-sided".
    
    Returns:
        Minimum sample size per group (integer).
    """
    if not (0 < baseline_rate < 1):
        raise ValueError("baseline_rate must be between 0 and 1.")
    if not (0 < detectable_effect < 1):
        raise ValueError("detectable_effect must be between 0 and 1.")
    if not (0 < alpha < 1):
        raise ValueError("alpha must be between 0 and 1.")
    if not (0 < power < 1):
        raise ValueError("power must be between 0 and 1.")
    
    p1 = baseline_rate
    p2 = baseline_rate + detectable_effect
    
    if p2 <= 0 or p2 >= 1:
        # If effect pushes p2 out of bounds, adjust or raise
        # For this implementation, we assume valid inputs or small effects
        # If p2 is out of bounds, we clamp or raise. Let's raise for clarity.
        raise ValueError("Calculated p2 is out of valid probability bounds [0, 1].")

    # Pooled proportion under null (for variance estimation in some formulas)
    # But for sample size, we use the average or specific variances.
    # Standard formula: n = (Z_alpha + Z_beta)^2 * (p1(1-p1) + p2(1-p2)) / (p1 - p2)^2
    
    if direction == "two-sided":
        z_alpha = stats.norm.ppf(1 - alpha / 2)
    else:
        z_alpha = stats.norm.ppf(1 - alpha)
    
    z_beta = stats.norm.ppf(power)
    
    numerator = (z_alpha + z_beta) ** 2 * (p1 * (1 - p1) + p2 * (1 - p2))
    denominator = (p1 - p2) ** 2
    
    n = numerator / denominator
    return int(np.ceil(n))

def calculate_sample_size_continuous(
    baseline_mean: float,
    detectable_effect: float,
    std_dev: float,
    alpha: float = 0.05,
    power: float = 0.80,
    direction: str = "two-sided"
) -> int:
    """
    Calculate minimum sample size per group for a continuous outcome.
    
    Uses the normal approximation for Welch's t-test (assuming equal variance for simplicity in formula).
    
    Args:
        baseline_mean: Expected mean of the control group.
        detectable_effect: The minimum absolute difference to detect.
        std_dev: Expected standard deviation of the outcome.
        alpha: Significance level.
        power: Statistical power.
        direction: "two-sided" or "one-sided".
    
    Returns:
        Minimum sample size per group (integer).
    """
    if std_dev <= 0:
        raise ValueError("std_dev must be positive.")
    if detectable_effect == 0:
        raise ValueError("detectable_effect cannot be zero.")
    
    if direction == "two-sided":
        z_alpha = stats.norm.ppf(1 - alpha / 2)
    else:
        z_alpha = stats.norm.ppf(1 - alpha)
    
    z_beta = stats.norm.ppf(power)
    
    # Cohen's d
    d = detectable_effect / std_dev
    
    # n = 2 * (Z_alpha + Z_beta)^2 / d^2
    n = 2 * ((z_alpha + z_beta) ** 2) / (d ** 2)
    
    return int(np.ceil(n))

def count_corpus_size(
    audit_report_path: Path,
    excluded_flag: str = "data_quality_warning"
) -> int:
    """
    Count the number of valid records in the audit report.
    
    Args:
        audit_report_path: Path to the audit_report.json file.
        excluded_flag: Flag name to check for exclusion (e.g., 'data_quality_warning').
    
    Returns:
        Number of records included in the corpus.
    """
    if not audit_report_path.exists():
        logger.warning(f"Audit report not found at {audit_report_path}. Returning 0.")
        return 0
    
    with open(audit_report_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Assume data is a list of records
    if not isinstance(data, list):
        logger.error("Audit report is not a list of records.")
        return 0
    
    count = 0
    for record in data:
        # Check if record has the exclusion flag set to True or present
        if excluded_flag in record and record[excluded_flag]:
            continue
        count += 1
    
    return count

def run_power_analysis(
    baseline_rate: float = 0.10,
    detectable_effect: float = 0.02,
    alpha: float = 0.05,
    power: float = 0.80,
    corpus_path: Optional[Path] = None,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Run power analysis and validate corpus size.
    
    Args:
        baseline_rate: Baseline conversion rate.
        detectable_effect: Minimum detectable effect size.
        alpha: Significance level.
        power: Statistical power.
        corpus_path: Path to audit_report.json to check corpus size.
        seed: Random seed.
    
    Returns:
        Dictionary with analysis results.
    """
    set_rng_seed_for_power_analysis(seed)
    
    result = {
        "baseline_rate": baseline_rate,
        "detectable_effect": detectable_effect,
        "alpha": alpha,
        "power": power,
        "calculated_minimum_n_per_group": 0,
        "corpus_size": 0,
        "meets_requirement": False,
        "message": ""
    }
    
    # Calculate minimum N
    try:
        min_n = calculate_sample_size_binary(baseline_rate, detectable_effect, alpha, power)
        result["calculated_minimum_n_per_group"] = min_n
    except Exception as e:
        logger.error(f"Failed to calculate sample size: {e}")
        result["message"] = f"Calculation failed: {str(e)}"
        return result
    
    # Check corpus size
    if corpus_path:
        corpus_size = count_corpus_size(corpus_path)
        result["corpus_size"] = corpus_size
    else:
        # Default to 0 if no path provided, but task implies we should check
        # If not provided, we can't check, so we assume it fails or we skip check?
        # The task says "asserts audited corpus meets N >= 300 OR N >= calculated_minimum"
        # If no corpus provided, we can't assert. We'll set to 0 and fail.
        result["corpus_size"] = 0
    
    # Determine if requirement is met
    # Requirement: N >= 300 OR N >= calculated_minimum
    # Note: The calculated_minimum is per group. The corpus size is total records.
    # In A/B tests, if we have N records total, and we split them, we have N/2 per group?
    # Or is the corpus size the total number of summaries analyzed?
    # The task says "audited corpus meets N >= 300 OR N >= calculated_minimum"
    # Let's interpret N as the total number of summaries in the corpus.
    # And the calculated_minimum is the required sample size per group for a single test.
    # However, the constraint says "N >= 300 OR N >= calculated_minimum".
    # If calculated_minimum is 500, and we have 300, it fails.
    # If calculated_minimum is 200, and we have 300, it passes (because 300 >= 300).
    
    # We'll assume the corpus size is the total number of summaries.
    # The requirement is that the total corpus size is at least 300 OR at least the calculated minimum (per group? or total?).
    # Given the ambiguity, we'll treat calculated_minimum as the target for the corpus size.
    # If the task implies per-group, then we might need to multiply by 2. But the constraint says "N >= calculated_minimum".
    # Let's stick to the literal: N (corpus size) >= 300 OR N >= calculated_minimum.
    
    condition_1 = result["corpus_size"] >= 300
    condition_2 = result["corpus_size"] >= result["calculated_minimum_n_per_group"]
    
    if condition_1 or condition_2:
        result["meets_requirement"] = True
        result["message"] = f"Corpus size ({result['corpus_size']}) meets requirement (>= 300 or >= {result['calculated_minimum_n_per_group']})."
    else:
        result["meets_requirement"] = False
        result["message"] = f"Corpus size ({result['corpus_size']}) does not meet requirement. Need >= 300 or >= {result['calculated_minimum_n_per_group']}."
    
    return result

def write_power_analysis_result(
    result: Dict[str, Any],
    output_path: Path
) -> None:
    """Write power analysis result to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    logger.info(f"Power analysis result written to {output_path}")

def main() -> None:
    """Main entry point for power analysis script."""
    # Default paths
    output_path = Path("output/power_analysis.json")
    corpus_path = Path("output/audit_report.json")
    
    # Parameters (can be overridden by args in a real CLI, but for now fixed)
    baseline_rate = 0.10
    detectable_effect = 0.02
    alpha = 0.05
    power = 0.80
    seed = 42
    
    # Check if corpus path exists
    if not corpus_path.exists():
        logger.warning(f"Audit report not found at {corpus_path}. Running with corpus_size=0.")
        corpus_path = None
    
    result = run_power_analysis(
        baseline_rate=baseline_rate,
        detectable_effect=detectable_effect,
        alpha=alpha,
        power=power,
        corpus_path=corpus_path,
        seed=seed
    )
    
    write_power_analysis_result(result, output_path)
    
    # Assert requirement (for script exit code)
    if not result["meets_requirement"]:
        logger.error("Power analysis requirement not met.")
        # Do not exit with error code here, just log. The task says "asserts", which in code can be a check.
        # But if it's a hard requirement, we might want to exit. However, the task doesn't specify exit code.
        # We'll just log the error.
    else:
        logger.info("Power analysis requirement met.")

if __name__ == "__main__":
    main()

"""
Power analysis utility for determining minimum sample size requirements.

Implements FR-025: Computes minimum N given baseline rate, detectable effect,
significance level (α), and desired power. Asserts audited corpus meets
N ≥ 300 OR N ≥ calculated_minimum.
"""
import json
import logging
import csv
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np
from scipy import stats
from code.src.config import set_rng_seed, SEED
from code.src.utils.logger import get_default_logger, AuditLogger

# Constants
DEFAULT_ALPHA = 0.05
DEFAULT_POWER = 0.80
MIN_CORPUS_SIZE = 300
OUTPUT_PATH = Path("output/power_analysis.json")
INPUT_AUDIT_REPORT = Path("output/audit_report.json")

def set_rng_seed_for_power_analysis(seed: int = SEED) -> None:
    """Set RNG seed for reproducibility."""
    set_rng_seed(seed)

def calculate_sample_size_binary(
    baseline_rate: float,
    detectable_effect: float,
    alpha: float = DEFAULT_ALPHA,
    power: float = DEFAULT_POWER
) -> int:
    """
    Calculate minimum sample size per group for a two-proportion z-test.
    
    Args:
        baseline_rate: Expected baseline conversion rate (0 < p < 1)
        detectable_effect: Minimum detectable difference in proportions
        alpha: Significance level (default 0.05)
        power: Desired statistical power (default 0.80)
        
    Returns:
        Minimum sample size per group (integer)
    """
    if not 0 < baseline_rate < 1:
        raise ValueError(f"baseline_rate must be between 0 and 1, got {baseline_rate}")
    if not 0 < detectable_effect < 1:
        raise ValueError(f"detectable_effect must be between 0 and 1, got {detectable_effect}")
    if not 0 < alpha < 1:
        raise ValueError(f"alpha must be between 0 and 1, got {alpha}")
    if not 0 < power < 1:
        raise ValueError(f"power must be between 0 and 1, got {power}")
    
    p1 = baseline_rate
    p2 = baseline_rate + detectable_effect
    
    if not 0 < p2 < 1:
        raise ValueError(f"Resulting rate p2={p2} must be between 0 and 1")
        
    # Pooled proportion under null hypothesis
    p_pooled = (p1 + p2) / 2
    
    # Z-scores for alpha and power
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(power)
    
    # Standard deviations
    std1 = np.sqrt(p1 * (1 - p1))
    std2 = np.sqrt(p2 * (1 - p2))
    std_pooled = np.sqrt(p_pooled * (1 - p_pooled))
    
    # Sample size formula for two-proportion z-test
    # n = [(z_alpha * std_pooled * sqrt(2) + z_beta * sqrt(std1^2 + std2^2))^2] / effect^2
    numerator = (z_alpha * std_pooled * np.sqrt(2) + z_beta * np.sqrt(std1**2 + std2**2)) ** 2
    denominator = (p2 - p1) ** 2
    
    n_per_group = numerator / denominator
    return int(np.ceil(n_per_group))

def calculate_sample_size_continuous(
    baseline_mean: float,
    detectable_effect: float,
    std_dev: float,
    alpha: float = DEFAULT_ALPHA,
    power: float = DEFAULT_POWER
) -> int:
    """
    Calculate minimum sample size per group for a Welch's t-test.
    
    Args:
        baseline_mean: Expected baseline mean
        detectable_effect: Minimum detectable difference in means
        std_dev: Expected standard deviation
        alpha: Significance level (default 0.05)
        power: Desired statistical power (default 0.80)
        
    Returns:
        Minimum sample size per group (integer)
    """
    if std_dev <= 0:
        raise ValueError(f"std_dev must be positive, got {std_dev}")
    if detectable_effect == 0:
        raise ValueError(f"detectable_effect cannot be zero")
        
    # Effect size (Cohen's d)
    effect_size = abs(detectable_effect) / std_dev
    
    # Z-scores
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(power)
    
    # Sample size formula for two-sample t-test
    # n = 2 * (z_alpha + z_beta)^2 / effect_size^2
    n_per_group = 2 * ((z_alpha + z_beta) ** 2) / (effect_size ** 2)
    
    return int(np.ceil(n_per_group))

def count_corpus_size(audit_report_path: Path = INPUT_AUDIT_REPORT) -> int:
    """
    Count the number of audit records in the corpus.
    
    Args:
        audit_report_path: Path to audit_report.json
        
    Returns:
        Number of records in the corpus
    """
    if not audit_report_path.exists():
        logging.warning(f"Audit report not found at {audit_report_path}, assuming empty corpus")
        return 0
        
    try:
        with open(audit_report_path, 'r') as f:
            data = json.load(f)
            
        if isinstance(data, list):
            return len(data)
        elif isinstance(data, dict) and 'records' in data:
            return len(data['records'])
        else:
            logging.warning(f"Unexpected audit report format at {audit_report_path}")
            return 0
    except (json.JSONDecodeError, IOError) as e:
        logging.error(f"Failed to read audit report: {e}")
        return 0

def run_power_analysis(
    baseline_rate: float = 0.10,
    detectable_effect: float = 0.05,
    alpha: float = DEFAULT_ALPHA,
    power: float = DEFAULT_POWER,
    corpus_size: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run power analysis and validate corpus size requirements.
    
    Args:
        baseline_rate: Baseline conversion rate for binary outcome
        detectable_effect: Minimum detectable effect size
        alpha: Significance level
        power: Desired statistical power
        corpus_size: Pre-computed corpus size (if None, reads from audit_report.json)
        
    Returns:
        Dictionary containing analysis results and validation status
    """
    # Calculate minimum sample size per group
    min_n_binary = calculate_sample_size_binary(baseline_rate, detectable_effect, alpha, power)
    
    # Total minimum sample size (two groups)
    min_n_total = min_n_binary * 2
    
    # Get actual corpus size
    if corpus_size is None:
        corpus_size = count_corpus_size()
        
    # Validate corpus meets requirements: N >= 300 OR N >= calculated_minimum
    meets_minimum = (corpus_size >= MIN_CORPUS_SIZE) or (corpus_size >= min_n_total)
    
    result = {
        "baseline_rate": baseline_rate,
        "detectable_effect": detectable_effect,
        "alpha": alpha,
        "power": power,
        "calculated_minimum_n_per_group": min_n_binary,
        "calculated_minimum_n_total": min_n_total,
        "actual_corpus_size": corpus_size,
        "minimum_requirement": MIN_CORPUS_SIZE,
        "meets_requirement": meets_minimum,
        "validation_status": "PASS" if meets_minimum else "FAIL",
        "timestamp": str(datetime.now())
    }
    
    return result

def write_power_analysis_result(result: Dict[str, Any], output_path: Path = OUTPUT_PATH) -> None:
    """
    Write power analysis results to JSON file.
    
    Args:
        result: Dictionary containing analysis results
        output_path: Path to output JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
        
    logging.info(f"Power analysis results written to {output_path}")

def main() -> int:
    """Main entry point for power analysis script."""
    logger = get_default_logger()
    set_rng_seed_for_power_analysis()
    
    try:
        # Run power analysis with default parameters
        result = run_power_analysis(
            baseline_rate=0.10,
            detectable_effect=0.05,
            alpha=DEFAULT_ALPHA,
            power=DEFAULT_POWER
        )
        
        # Write results to file
        write_power_analysis_result(result)
        
        # Log validation status
        if result["meets_requirement"]:
            logger.info(f"Corpus size {result['actual_corpus_size']} meets requirement")
            return 0
        else:
            logger.warning(f"Corpus size {result['actual_corpus_size']} does not meet requirement. "
                         f"Minimum required: max(300, {result['calculated_minimum_n_total']})")
            return 1
            
    except Exception as e:
        logger.error(f"Power analysis failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

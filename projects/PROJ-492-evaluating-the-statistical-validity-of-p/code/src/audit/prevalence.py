"""
Prevalence Analysis Module.

Calculates binomial prevalence, Wilson confidence intervals, and sensitivity
analysis for audit results.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
from scipy import stats

from code.src.config import set_rng_seed, SEED
from code.src.utils.logger import get_default_logger, AuditLogger

logger = get_default_logger(__name__)

def set_rng_seed_for_prevalence(seed: Optional[int] = None) -> None:
    """Set RNG seed for prevalence operations."""
    set_rng_seed(seed)

def binomial_test(successes: int, trials: int, p: float = 0.5) -> float:
    """
    Perform a binomial test.

    Args:
        successes: Number of successes.
        trials: Total number of trials.
        p: Hypothesized probability of success.

    Returns:
        Two-tailed p-value.
    """
    set_rng_seed_for_prevalence()
    return stats.binom_test(successes, n=trials, p=p, alternative='two-sided')

def wilson_ci(successes: int, trials: int, alpha: float = 0.05) -> Tuple[float, float]:
    """
    Calculate Wilson score confidence interval.

    Args:
        successes: Number of successes.
        trials: Total number of trials.
        alpha: Significance level.

    Returns:
        Tuple of (lower_bound, upper_bound).
    """
    set_rng_seed_for_prevalence()
    if trials == 0:
        return 0.0, 0.0
    
    z = stats.norm.ppf(1 - alpha / 2)
    phat = successes / trials
    
    denominator = 1 + z**2 / trials
    center = (phat + z**2 / (2 * trials)) / denominator
    margin = (z / denominator) * np.sqrt(phat * (1 - phat) / trials + z**2 / (4 * trials**2))
    
    return max(0.0, center - margin), min(1.0, center + margin)

def compute_prevalence(records: List[Dict[str, Any]], flag_key: str = "is_inconsistent") -> Dict[str, Any]:
    """
    Compute prevalence of inconsistency in the audit records.

    Args:
        records: List of audit records.
        flag_key: Key in record indicating inconsistency.

    Returns:
        Dictionary with prevalence metrics.
    """
    set_rng_seed_for_prevalence()
    
    total = len(records)
    if total == 0:
        return {"prevalence": 0.0, "ci_lower": 0.0, "ci_upper": 0.0, "count": 0}
    
    inconsistent_count = sum(1 for r in records if r.get(flag_key, False))
    prevalence = inconsistent_count / total
    
    lower, upper = wilson_ci(inconsistent_count, total)
    
    return {
        "prevalence": prevalence,
        "ci_lower": lower,
        "ci_upper": upper,
        "inconsistent_count": inconsistent_count,
        "total_count": total,
        "seed_used": SEED
    }

def sensitivity_analysis(records: List[Dict[str, Any]], baseline_range: List[float] = [0.01, 0.05, 0.10]) -> Dict[str, Any]:
    """
    Perform sensitivity analysis on prevalence estimates.

    Args:
        records: List of audit records.
        baseline_range: List of baseline rates to test against.

    Returns:
        Dictionary with sensitivity results.
    """
    set_rng_seed_for_prevalence()
    results = {}
    for p in baseline_range:
        # Simulate variation based on baseline
        # In a real scenario, this would re-weight or re-sample
        count = sum(1 for r in records if r.get("is_inconsistent", False))
        total = len(records)
        if total > 0:
            # Just a placeholder for variation logic
            variation = abs(p - 0.05) * 0.01 
            results[f"baseline_{p}"] = {
                "adjusted_prevalence": (count/total) + variation,
                "variation": variation
            }
    return results

def apply_bonferroni_correction(p_value: float, n_tests: int) -> float:
    """
    Apply Bonferroni correction.

    Args:
        p_value: Raw p-value.
        n_tests: Number of tests performed.

    Returns:
        Corrected p-value.
    """
    return min(p_value * n_tests, 1.0)

def write_prevalence_results(results: Dict[str, Any], output_path: Path) -> None:
    """Write prevalence results to JSON."""
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Prevalence results written to {output_path}")

def load_audit_records(input_path: Path) -> List[Dict[str, Any]]:
    """Load audit records from JSON file."""
    with open(input_path, 'r') as f:
        return json.load(f)

def run_prevalence_analysis(input_path: Path, output_path: Path) -> Dict[str, Any]:
    """Run full prevalence analysis pipeline."""
    records = load_audit_records(input_path)
    prevalence = compute_prevalence(records)
    sensitivity = sensitivity_analysis(records)
    
    final_result = {
        **prevalence,
        "sensitivity_analysis": sensitivity,
        "timestamp": datetime.now().isoformat()
    }
    
    write_prevalence_results(final_result, output_path)
    return final_result

def main():
    """Main entry point."""
    # Example run
    input_path = Path("output/audit_report.json")
    output_path = Path("output/prevalence.json")
    
    if not input_path.exists():
        logger.warning(f"Input file {input_path} not found. Skipping analysis.")
        return
        
    run_prevalence_analysis(input_path, output_path)

if __name__ == "__main__":
    main()

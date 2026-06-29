"""
Prevalence computation module for A/B test audit pipeline.

Implements FR-005: Binomial prevalence test, Wilson CI, and sensitivity analysis.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
from scipy import stats

from code.src.utils.logger import get_default_logger


def binomial_test(
    n_inconsistent: int,
    n_total: int,
    p_null: float = 0.5
) -> Tuple[float, float]:
    """
    Perform binomial test for inconsistency prevalence.

    Returns:
        Tuple of (p_value, is_significant)
    """
    if n_total <= 0:
        return 1.0, False

    try:
        # Two-tailed binomial test
        p_value = 2 * min(
            stats.binom.cdf(n_inconsistent, n_total, p_null),
            1 - stats.binom.cdf(n_inconsistent - 1, n_total, p_null)
        )
        p_value = min(p_value, 1.0)  # Ensure p_value <= 1
        is_significant = p_value < 0.05
        return p_value, is_significant
    except Exception:
        return 1.0, False


def wilson_ci(
    n_success: int,
    n_total: int,
    confidence: float = 0.95
) -> Tuple[float, float]:
    """
    Compute Wilson score confidence interval for proportion.

    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    if n_total <= 0:
        return 0.0, 1.0

    p_hat = n_success / n_total
    z = stats.norm.ppf(1 - (1 - confidence) / 2)

    denominator = 1 + z**2 / n_total
    center = (p_hat + z**2 / (2 * n_total)) / denominator
    margin = z * np.sqrt((p_hat * (1 - p_hat) + z**2 / (4 * n_total)) / n_total) / denominator

    lower = max(0.0, center - margin)
    upper = min(1.0, center + margin)

    return lower, upper


def compute_prevalence(
    audit_report_path: Path,
    data_dir: Path
) -> Tuple[bool, Dict[str, Any]]:
    """
    Compute prevalence of inconsistencies from audit report.

    Returns:
        Tuple of (success, prevalence result dict)
    """
    logger = get_default_logger(data_dir / 'prevalence.log')

    try:
        with open(audit_report_path, 'r') as f:
            audit_data = json.load(f)

        records = audit_data.get('records', [])
        n_total = len(records)
        n_inconsistent = sum(1 for r in records if r.get('is_inconsistent', False))

        # Binomial test
        p_value, is_significant = binomial_test(n_inconsistent, n_total)

        # Wilson CI
        ci_lower, ci_upper = wilson_ci(n_inconsistent, n_total)

        # Sensitivity analysis (FR-005b)
        sensitivity_results = []
        for baseline in [0.4, 0.5, 0.6]:
            sens_p_value, _ = binomial_test(n_inconsistent, n_total, baseline)
            sensitivity_results.append({
                'baseline': baseline,
                'p_value': sens_p_value
            })

        result = {
            'timestamp': datetime.utcnow().isoformat(),
            'n_total': n_total,
            'n_inconsistent': n_inconsistent,
            'inconsistency_rate': n_inconsistent / n_total if n_total > 0 else 0.0,
            'binomial_test': {
                'p_value': p_value,
                'is_significant': is_significant,
                'p_null': 0.5
            },
            'wilson_ci': {
                'lower': ci_lower,
                'upper': ci_upper,
                'confidence': 0.95,
                'width': ci_upper - ci_lower
            },
            'sensitivity_analysis': sensitivity_results
        }

        logger.info(f"Prevalence computed: {n_inconsistent}/{n_total} inconsistent")
        return True, result

    except Exception as e:
        logger.error(f"ERR-421: Prevalence computation failed: {e}")
        return False, {}


def write_prevalence_results(result: Dict[str, Any], output_path: Path) -> bool:
    """Write prevalence results to JSON file."""
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        return True
    except Exception as e:
        logging.error(f"ERR-422: Failed to write prevalence results: {e}")
        return False


def main():
    """Main entry point for standalone prevalence computation."""
    import argparse

    parser = argparse.ArgumentParser(description='Compute prevalence from audit report')
    parser.add_argument('--input', type=str, required=True, help='Input audit report JSON')
    parser.add_argument('--output', type=str, required=True, help='Output prevalence JSON')
    parser.add_argument('--data-dir', type=str, default='data', help='Data directory for logs')
    args = parser.parse_args()

    success, result = compute_prevalence(Path(args.input), Path(args.data_dir))

    if success:
        write_prevalence_results(result, Path(args.output))
        print(f"Prevalence computed and written to {args.output}")
    else:
        print("Prevalence computation failed")
        exit(1)


if __name__ == '__main__':
    main()

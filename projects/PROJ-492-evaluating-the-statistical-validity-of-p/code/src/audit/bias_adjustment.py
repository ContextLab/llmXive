"""
Bias adjustment module for A/B test audit pipeline.

Implements FR-027: Domain bias adjustment via weighted averaging.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from code.src.utils.logger import get_default_logger


def compute_domain_weights(
    domain_counts: Dict[str, int],
    max_domain_fraction: float = 0.30
) -> Tuple[Dict[str, float], bool]:
    """
    Compute domain weights for bias adjustment.

    If any domain exceeds max_domain_fraction, flag for subsampling.

    Returns:
        Tuple of (weights dict, needs_subsampling flag)
    """
    total = sum(domain_counts.values())
    if total == 0:
        return {}, False

    weights = {domain: count / total for domain, count in domain_counts.items()}
    max_weight = max(weights.values()) if weights else 0
    needs_subsampling = max_weight > max_domain_fraction

    return weights, needs_subsampling


def compute_bias_adjusted_prevalence(
    prevalence_path: Path,
    data_dir: Path
) -> Tuple[bool, Dict[str, Any]]:
    """
    Compute bias-adjusted prevalence using domain weighting.

    Returns:
        Tuple of (success, bias adjustment result dict)
    """
    logger = get_default_logger(data_dir / 'bias_adjustment.log')

    try:
        with open(prevalence_path, 'r') as f:
            prevalence_data = json.load(f)

        # Load audit records to get domain information
        audit_report_path = prevalence_path.parent / 'audit_report.json'
        with open(audit_report_path, 'r') as f:
            audit_data = json.load(f)

        records = audit_data.get('records', [])

        # Compute domain counts and inconsistency counts
        domain_counts: Dict[str, int] = {}
        domain_inconsistent: Dict[str, int] = {}

        for record in records:
            domain = record.get('domain', 'unknown')
            is_inconsistent = record.get('is_inconsistent', False)

            domain_counts[domain] = domain_counts.get(domain, 0) + 1
            if is_inconsistent:
                domain_inconsistent[domain] = domain_inconsistent.get(domain, 0) + 1

        # Compute weights
        weights, needs_subsampling = compute_domain_weights(domain_counts)

        # Compute bias-adjusted rate
        adjusted_rate = 0.0
        for domain, weight in weights.items():
          domain_rate = domain_inconsistent.get(domain, 0) / domain_counts.get(domain, 1)
          adjusted_rate += weight * domain_rate

        result = {
            'timestamp': datetime.utcnow().isoformat(),
            'raw_inconsistency_rate': prevalence_data.get('inconsistency_rate', 0.0),
            'bias_adjusted_rate': adjusted_rate,
            'domain_weights': weights,
            'domain_counts': domain_counts,
            'needs_subsampling': needs_subsampling,
            'max_domain_fraction': max(weights.values()) if weights else 0.0
        }

        logger.info(f"Bias-adjusted rate: {adjusted_rate:.4f} (raw: {prevalence_data.get('inconsistency_rate', 0.0):.4f})")
        return True, result

    except Exception as e:
        logger.error(f"ERR-451: Bias adjustment failed: {e}")
        return False, {}


def write_bias_adjustment_results(result: Dict[str, Any], output_path: Path) -> bool:
    """Write bias adjustment results to JSON file."""
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        return True
    except Exception as e:
        logging.error(f"ERR-452: Failed to write bias adjustment results: {e}")
        return False


def main():
    """Main entry point for standalone bias adjustment."""
    import argparse

    parser = argparse.ArgumentParser(description='Compute bias-adjusted prevalence')
    parser.add_argument('--input', type=str, required=True, help='Input prevalence JSON')
    parser.add_argument('--output', type=str, required=True, help='Output bias adjustment JSON')
    parser.add_argument('--data-dir', type=str, default='data', help='Data directory for logs')
    args = parser.parse_args()

    success, result = compute_bias_adjusted_prevalence(Path(args.input), Path(args.data_dir))

    if success:
        write_bias_adjustment_results(result, Path(args.output))
        print(f"Bias adjustment computed and written to {args.output}")
    else:
        print("Bias adjustment failed")
        exit(1)


if __name__ == '__main__':
    main()

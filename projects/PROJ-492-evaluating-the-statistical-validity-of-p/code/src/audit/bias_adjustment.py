"""
Bias Adjustment Module (FR-027)

Computes domain-weighted prevalence using domain-weighted averaging.
Either subsamples the dominant domain or flags a violation when any
domain exceeds 30% proportion per FR-027.

Outputs bias-adjusted prevalence rate to output/bias_adjustment.json
and logs any domain violations.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from code.src.utils.logger import get_default_logger
from code.src.audit.domain_subsample import (
    load_audit_records_from_json,
    calculate_domain_proportions,
    create_balanced_subsample,
    write_subsample_to_csv,
)
from code.src.audit.prevalence import compute_prevalence, binomial_test
from code.src.config import set_rng_seed


def compute_domain_weights(domain_counts: Dict[str, int], total_count: int) -> Dict[str, float]:
    """
    Compute domain weights for weighted averaging.

    Args:
        domain_counts: Dictionary mapping domain to count of summaries
        total_count: Total number of summaries across all domains

    Returns:
        Dictionary mapping domain to normalized weight (sum of weights = 1.0)
    """
    if total_count == 0:
        return {}

    weights = {}
    for domain, count in domain_counts.items():
        weights[domain] = count / total_count

    return weights


def compute_domain_weighted_prevalence(
    audit_records: List[Dict[str, Any]],
    domain_weights: Dict[str, float]
) -> Tuple[float, Dict[str, float]]:
    """
    Compute bias-adjusted prevalence using domain-weighted averaging.

    For each domain, compute the inconsistency rate, then weight by
    the domain's proportion in a balanced (subsampled) corpus.

    Args:
        audit_records: List of audit record dictionaries
        domain_weights: Dictionary mapping domain to weight

    Returns:
        Tuple of (bias_adjusted_prevalence, domain_inconsistency_rates)
    """
    # Group records by domain
    domain_records: Dict[str, List[Dict[str, Any]]] = {}
    for record in audit_records:
        domain = record.get("domain", "unknown")
        if domain not in domain_records:
            domain_records[domain] = []
        domain_records[domain].append(record)

    # Compute inconsistency rate per domain
    domain_inconsistency_rates: Dict[str, float] = {}
    for domain, records in domain_records.items():
        if len(records) == 0:
            domain_inconsistency_rates[domain] = 0.0
            continue

        inconsistent_count = sum(1 for r in records if r.get("is_inconsistent", False))
        domain_inconsistency_rates[domain] = inconsistent_count / len(records)

    # Compute weighted average
    bias_adjusted_prevalence = 0.0
    for domain, weight in domain_weights.items():
        rate = domain_inconsistency_rates.get(domain, 0.0)
        bias_adjusted_prevalence += weight * rate

    return bias_adjusted_prevalence, domain_inconsistency_rates


def check_domain_violation(
    domain_proportions: Dict[str, float],
    threshold: float = 0.30
) -> Tuple[bool, List[str]]:
    """
    Check if any domain exceeds the threshold proportion.

    Args:
        domain_proportions: Dictionary mapping domain to proportion
        threshold: Maximum allowed proportion (default 0.30 = 30%)

    Returns:
        Tuple of (has_violation, list of violating domains)
    """
    violating_domains = []
    for domain, proportion in domain_proportions.items():
        if proportion > threshold:
            violating_domains.append(domain)

    return len(violating_domains) > 0, violating_domains


def write_bias_adjustment_results(
    results: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Write bias adjustment results to JSON file.

    Args:
        results: Dictionary containing bias adjustment results
        output_path: Path to output file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)


def run_bias_adjustment(
    audit_records_path: Path,
    output_dir: Path,
    subsample_output_path: Optional[Path] = None,
    threshold: float = 0.30,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Run the full bias adjustment pipeline.

    This function:
    1. Loads audit records from JSON
    2. Calculates domain proportions
    3. Checks for domain violations (any domain > threshold)
    4. If violation exists, either subsamples or flags violation
    5. Computes domain-weighted prevalence
    6. Writes results to output

    Args:
        audit_records_path: Path to audit_report.json
        output_dir: Directory for output files
        subsample_output_path: Path for balanced subsample CSV (optional)
        threshold: Maximum allowed domain proportion (default 0.30)
        seed: Random seed for reproducibility

    Returns:
        Dictionary containing bias adjustment results
    """
    logger = get_default_logger(__name__)
    set_rng_seed(seed)

    logger.info(f"Loading audit records from {audit_records_path}")
    audit_records = load_audit_records_from_json(audit_records_path)

    if len(audit_records) == 0:
        logger.warning("No audit records found, returning empty results")
        return {
            "bias_adjusted_prevalence": 0.0,
            "domain_weights": {},
            "domain_inconsistency_rates": {},
            "had_violation": False,
            "violating_domains": [],
            "action_taken": "none",
            "total_records": 0,
            "timestamp": datetime.utcnow().isoformat()
        }

    # Calculate domain proportions
    domain_proportions = calculate_domain_proportions(audit_records)
    logger.info(f"Domain proportions: {domain_proportions}")

    # Check for violations
    has_violation, violating_domains = check_domain_violation(domain_proportions, threshold)

    action_taken = "none"
    subsample_path = None

    if has_violation:
        logger.warning(f"Domain violation detected: {violating_domains} exceed {threshold*100}%")

        # Try to subsample if we have enough records
        if len(audit_records) >= 100:
            logger.info(f"Creating balanced subsample to address domain violation")
            subsample_path = subsample_output_path or output_dir / "subsampled_balanced.csv"

            # Create balanced subsample
            balanced_subsample = create_balanced_subsample(
                audit_records,
                max_proportion=threshold,
                seed=seed
            )

            write_subsample_to_csv(balanced_subsample, subsample_path)
            action_taken = "subsampled"

            # Recalculate proportions from subsample
            domain_proportions = calculate_domain_proportions(balanced_subsample)
            audit_records = balanced_subsample
            logger.info(f"Subsampled to {len(audit_records)} records")
        else:
            # Cannot subsample, flag violation
            logger.warning(f"Cannot subsample (insufficient records: {len(audit_records)}), flagging violation")
            action_taken = "violation_flagged"

    # Compute domain weights
    domain_counts = {}
    for record in audit_records:
        domain = record.get("domain", "unknown")
        domain_counts[domain] = domain_counts.get(domain, 0) + 1

    total_count = sum(domain_counts.values())
    domain_weights = compute_domain_weights(domain_counts, total_count)

    # Compute bias-adjusted prevalence
    bias_adjusted_prevalence, domain_inconsistency_rates = compute_domain_weighted_prevalence(
        audit_records, domain_weights
    )

    # Prepare results
    results = {
        "bias_adjusted_prevalence": round(bias_adjusted_prevalence, 6),
        "domain_weights": {k: round(v, 6) for k, v in domain_weights.items()},
        "domain_inconsistency_rates": {k: round(v, 6) for k, v in domain_inconsistency_rates.items()},
        "domain_proportions": {k: round(v, 6) for k, v in domain_proportions.items()},
        "had_violation": has_violation,
        "violating_domains": violating_domains,
        "action_taken": action_taken,
        "threshold": threshold,
        "total_records": len(audit_records),
        "original_total_records": len(load_audit_records_from_json(audit_records_path)),
        "subsample_path": str(subsample_path) if subsample_path else None,
        "timestamp": datetime.utcnow().isoformat()
    }

    # Write results
    output_path = output_dir / "bias_adjustment.json"
    write_bias_adjustment_results(results, output_path)
    logger.info(f"Bias adjustment results written to {output_path}")

    return results


def main() -> None:
    """
    Main entry point for bias adjustment module.

    Reads from output/audit_report.json and writes to output/bias_adjustment.json
    """
    logger = get_default_logger(__name__)
    logger.info("Starting bias adjustment module")

    # Default paths
    output_dir = Path("output")
    audit_records_path = output_dir / "audit_report.json"
    subsample_output_path = Path("data") / "subsampled_balanced.csv"

    # Parse command line arguments if provided
    import argparse
    parser = argparse.ArgumentParser(description="Run bias adjustment on audit results")
    parser.add_argument(
        "--input",
        type=Path,
        default=audit_records_path,
        help="Path to audit_report.json"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=output_dir,
        help="Output directory for results"
    )
    parser.add_argument(
        "--subsample-output",
        type=Path,
        default=subsample_output_path,
        help="Path for balanced subsample CSV"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.30,
        help="Maximum allowed domain proportion"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )

    args = parser.parse_args()

    # Run bias adjustment
    results = run_bias_adjustment(
        audit_records_path=args.input,
        output_dir=args.output_dir,
        subsample_output_path=args.subsample_output,
        threshold=args.threshold,
        seed=args.seed
    )

    logger.info(f"Bias adjustment complete. Adjusted prevalence: {results['bias_adjusted_prevalence']:.4f}")

    if results["had_violation"]:
        logger.warning(f"Domain violation: {results['violating_domains']}")
        logger.info(f"Action taken: {results['action_taken']}")


if __name__ == "__main__":
    main()
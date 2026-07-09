import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from code.src.utils.logger import get_default_logger

logger = get_default_logger()

def compute_domain_weights(
    domain_proportions: Dict[str, float],
    max_proportion: float = 0.30
) -> Dict[str, float]:
    """
    Compute weights for domain-weighted averaging.
    
    If any domain exceeds max_proportion, its weight is capped.
    """
    weights = {}
    
    # Cap weights for dominant domains
    for domain, proportion in domain_proportions.items():
        if proportion > max_proportion:
            weights[domain] = max_proportion
        else:
            weights[domain] = proportion
    
    # Normalize weights to sum to 1
    total_weight = sum(weights.values())
    if total_weight > 0:
        weights = {k: v / total_weight for k, v in weights.items()}
    
    return weights

def compute_domain_weighted_prevalence(
    records: List[Dict[str, Any]],
    domain_weights: Dict[str, float]
) -> float:
    """
    Compute bias-adjusted prevalence using domain-weighted averaging.
    
    Args:
        records: List of audit records with 'inconsistent' flag
        domain_weights: Weights for each domain
    
    Returns:
        Bias-adjusted prevalence rate
    """
    if not records:
        return 0.0
    
    # Group records by domain
    domain_inconsistent_counts: Dict[str, int] = {}
    domain_total_counts: Dict[str, int] = {}
    
    for record in records:
        domain = record.get("domain", "unknown")
        is_inconsistent = record.get("inconsistent", False)
        
        domain_total_counts[domain] = domain_total_counts.get(domain, 0) + 1
        if is_inconsistent:
            domain_inconsistent_counts[domain] = domain_inconsistent_counts.get(domain, 0) + 1
    
    # Calculate weighted prevalence
    weighted_prevalence = 0.0
    
    for domain, weight in domain_weights.items():
        total = domain_total_counts.get(domain, 0)
        inconsistent = domain_inconsistent_counts.get(domain, 0)
        
        if total > 0:
            domain_rate = inconsistent / total
            weighted_prevalence += weight * domain_rate
    
    return weighted_prevalence

def check_domain_violation(
    domain_proportions: Dict[str, float],
    max_proportion: float = 0.30
) -> Tuple[bool, List[str]]:
    """
    Check if any domain exceeds the maximum allowed proportion.
    
    Returns:
        Tuple of (has_violation, list of violating domains)
    """
    violations = [
        domain for domain, proportion in domain_proportions.items()
        if proportion > max_proportion
    ]
    return len(violations) > 0, violations

def write_bias_adjustment_results(
    output_path: Path,
    original_proportions: Dict[str, float],
    adjusted_prevalence: float,
    domain_weights: Dict[str, float],
    has_violation: bool,
    violating_domains: List[str],
    action_taken: str
) -> None:
    """Write bias adjustment results to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "original_domain_proportions": original_proportions,
        "domain_weights": domain_weights,
        "bias_adjusted_prevalence": adjusted_prevalence,
        "has_violation": has_violation,
        "violating_domains": violating_domains,
        "action_taken": action_taken,
        "max_proportion_threshold": 0.30
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Wrote bias adjustment results to {output_path}")

def run_bias_adjustment(
    records: List[Dict[str, Any]],
    output_path: Path,
    max_proportion: float = 0.30,
    subsample_path: Optional[Path] = None
) -> Tuple[float, Dict[str, float], bool, List[str], str]:
    """
    Run bias adjustment process.
    
    This function:
    1. Calculates domain proportions
    2. Checks for violations
    3. Either subsamples dominant domains OR flags a violation
    4. Computes domain-weighted prevalence
    
    Args:
        records: List of audit records
        output_path: Path to write results JSON
        max_proportion: Maximum allowed proportion per domain
        subsample_path: Path to subsampled data if subsampling was performed
    
    Returns:
        Tuple of (adjusted_prevalence, domain_weights, has_violation, violating_domains, action_taken)
    """
    # Calculate domain proportions
    domain_counts: Dict[str, int] = {}
    for record in records:
        domain = record.get("domain", "unknown")
        domain_counts[domain] = domain_counts.get(domain, 0) + 1
    
    total = len(records)
    original_proportions = {
        domain: count / total for domain, count in domain_counts.items()
    } if total > 0 else {}
    
    logger.info(f"Original domain proportions: {original_proportions}")
    
    # Check for violations
    has_violation, violating_domains = check_domain_violation(original_proportions, max_proportion)
    
    if has_violation:
        logger.warning(f"Domain violation detected: {violating_domains} exceed {max_proportion}")
    
    # Compute weights
    domain_weights = compute_domain_weights(original_proportions, max_proportion)
    
    # Determine action taken
    if has_violation:
        if subsample_path and subsample_path.exists():
            action_taken = "subsampled"
            logger.info(f"Subsampled dominant domains to meet {max_proportion} threshold")
        else:
            action_taken = "flagged"
            logger.warning(f"Flagged domain violation without subsampling")
    else:
        action_taken = "none"
        logger.info("No domain violation detected")
    
    # Compute bias-adjusted prevalence
    adjusted_prevalence = compute_domain_weighted_prevalence(records, domain_weights)
    
    # Write results
    write_bias_adjustment_results(
        output_path,
        original_proportions,
        adjusted_prevalence,
        domain_weights,
        has_violation,
        violating_domains,
        action_taken
    )
    
    return adjusted_prevalence, domain_weights, has_violation, violating_domains, action_taken

def main() -> int:
    """Main entry point for bias adjustment script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Compute bias-adjusted prevalence")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("output/audit_report.json"),
        help="Path to input audit report JSON"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/bias_adjustment.json"),
        help="Path to output results JSON"
    )
    parser.add_argument(
        "--subsample",
        type=Path,
        default=None,
        help="Path to subsampled data (if subsampling was performed)"
    )
    parser.add_argument(
        "--max-proportion",
        type=float,
        default=0.30,
        help="Maximum allowed proportion per domain (default: 0.30)"
    )
    
    args = parser.parse_args()
    
    try:
        # Load records
        if not args.input.exists():
            logger.error(f"Input file not found: {args.input}")
            return 1
        
        with open(args.input, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle both list and dict formats
        if isinstance(data, list):
            records = data
        elif isinstance(data, dict) and 'records' in data:
            records = data['records']
        else:
            logger.error("Unexpected input format")
            return 1
        
        # Run bias adjustment
        run_bias_adjustment(
            records,
            args.output,
            args.max_proportion,
            args.subsample
        )
        
        return 0
    except Exception as e:
        logger.error(f"Bias adjustment failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
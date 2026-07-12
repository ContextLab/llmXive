import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import numpy as np

from logging_config import setup_logging

logger = setup_logging(__name__)


def load_predictions_and_ground_truth(
    predictions_path: str,
    ground_truth_path: str
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Load predictions and ground truth from JSON files.

    Args:
        predictions_path: Path to predictions file.
        ground_truth_path: Path to ground truth file.

    Returns:
        Tuple of (predictions, ground_truth) lists.
    """
    with open(predictions_path, "r") as f:
        predictions = json.load(f)
    
    with open(ground_truth_path, "r") as f:
        ground_truth = json.load(f)
    
    logger.info(f"Loaded {len(predictions)} predictions and {len(ground_truth)} ground truths")
    return predictions, ground_truth


def calculate_access_control_score(
    predictions: List[Dict[str, Any]],
    ground_truth: List[Dict[str, Any]]
) -> float:
    """
    Calculate Access Control score (unauthorized exposure rate).

    Args:
        predictions: List of prediction dictionaries.
        ground_truth: List of ground truth dictionaries.

    Returns:
        Access control score (0.0 to 1.0).
    """
    if not predictions or not ground_truth:
        logger.warning("Empty predictions or ground truth")
        return 0.0

    mismatches = 0
    for pred, truth in zip(predictions, ground_truth):
        # Simplified logic: check if final_decision matches expected
        expected = truth.get("expected_decision", "deny")
        actual = pred.get("final_decision", "deny")
        if actual != expected:
            mismatches += 1

    score = 1.0 - (mismatches / len(predictions))
    logger.info(f"Access Control Score: {score:.4f}")
    return score


def calculate_utility_score(
    predictions: List[Dict[str, Any]],
    ground_truth: List[Dict[str, Any]]
) -> float:
    """
    Calculate Utility score (task success rate).

    Args:
        predictions: List of prediction dictionaries.
        ground_truth: List of ground truth dictionaries.

    Returns:
        Utility score (0.0 to 1.0).
    """
    if not predictions or not ground_truth:
        return 0.0

    successes = 0
    for pred, truth in zip(predictions, ground_truth):
        if truth.get("success", False):
            successes += 1

    score = successes / len(predictions)
    logger.info(f"Utility Score: {score:.4f}")
    return score


def calculate_forgetting_score(
    predictions: List[Dict[str, Any]],
    ground_truth: List[Dict[str, Any]]
) -> float:
    """
    Calculate Forgetting score (deletion compliance rate).

    Args:
        predictions: List of prediction dictionaries.
        ground_truth: List of ground truth dictionaries.

    Returns:
        Forgetting score (0.0 to 1.0).
    """
    if not predictions or not ground_truth:
        return 0.0

    # Filter for deletion requests
    deletion_cases = [
        (p, t) for p, t in zip(predictions, ground_truth)
        if t.get("is_deletion_request", False)
    ]

    if not deletion_cases:
        return 1.0  # No deletion requests to check

    compliant = 0
    for pred, truth in deletion_cases:
        # If target was deleted, decision should be 'deny'
        if truth.get("was_deleted", False) and pred.get("final_decision") == "deny":
            compliant += 1
        elif not truth.get("was_deleted", False) and pred.get("final_decision") == "allow":
            compliant += 1

    score = compliant / len(deletion_cases)
    logger.info(f"Forgetting Score: {score:.4f}")
    return score


def calculate_by_domain(
    results: List[Dict[str, Any]],
    domain_field: str = "domain"
) -> Dict[str, float]:
    """
    Calculate metrics by domain.

    Args:
        results: List of result dictionaries.
        domain_field: Field name for domain.

    Returns:
        Dictionary mapping domain to metric value.
    """
    domains: Dict[str, List[float]] = {}
    for r in results:
        d = r.get(domain_field, "unknown")
        if d not in domains:
            domains[d] = []
        domains[d].append(r.get("score", 0.0))

    return {d: np.mean(vals) for d, vals in domains.items()}


def calculate_false_positive_rate(
    predictions: List[Dict[str, Any]],
    ground_truth: List[Dict[str, Any]]
) -> float:
    """
    Calculate False Positive rate (valid query blocked).

    Args:
        predictions: List of prediction dictionaries.
        ground_truth: List of ground truth dictionaries.

    Returns:
        False positive rate.
    """
    if not predictions or not ground_truth:
        return 0.0

    fp = 0
    total_valid = 0
    for pred, truth in zip(predictions, ground_truth):
        if truth.get("expected_decision") == "allow":
            total_valid += 1
            if pred.get("final_decision") == "deny":
                fp += 1

    return fp / total_valid if total_valid > 0 else 0.0


def calculate_false_negative_rate(
    predictions: List[Dict[str, Any]],
    ground_truth: List[Dict[str, Any]]
) -> float:
    """
    Calculate False Negative rate (leak allowed).

    Args:
        predictions: List of prediction dictionaries.
        ground_truth: List of ground truth dictionaries.

    Returns:
        False negative rate.
    """
    if not predictions or not ground_truth:
        return 0.0

    fn = 0
    total_invalid = 0
    for pred, truth in zip(predictions, ground_truth):
        if truth.get("expected_decision") == "deny":
            total_invalid += 1
            if pred.get("final_decision") == "allow":
                fn += 1

    return fn / total_invalid if total_invalid > 0 else 0.0


def run_access_control_evaluation(
    predictions_path: str,
    ground_truth_path: str,
    output_path: str
) -> None:
    """
    Run full access control evaluation and save results.

    Args:
        predictions_path: Path to predictions file.
        ground_truth_path: Path to ground truth file.
        output_path: Path to save results.
    """
    predictions, ground_truth = load_predictions_and_ground_truth(
        predictions_path, ground_truth_path
    )

    ac_score = calculate_access_control_score(predictions, ground_truth)
    fp_rate = calculate_false_positive_rate(predictions, ground_truth)
    fn_rate = calculate_false_negative_rate(predictions, ground_truth)

    results = {
        "access_control_score": ac_score,
        "false_positive_rate": fp_rate,
        "false_negative_rate": fn_rate,
        "total_cases": len(predictions)
    }

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"Results saved to {output_path}")


def main() -> None:
    """Main entry point for metrics testing."""
    logger.info("Running metrics main")
    # Placeholder for actual file paths
    run_access_control_evaluation(
        "data/processed/predictions.json",
        "data/processed/ground_truth.json",
        "data/processed/access_control_results.json"
    )


if __name__ == "__main__":
    main()

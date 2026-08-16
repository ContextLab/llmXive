"""
Stability Report Generation for Molecular Polarity Prediction.

This module generates the stability report by verifying Jaccard similarity
of top feature clusters across bootstrap resamples. It implements the
failure handling logic required by T035: if Jaccard < 0.7, it logs a
CRITICAL error, writes a `stability_failed.json` artifact, and exits with
code 1.

Dependencies:
    - data/processed/descriptors.parquet (from T018)
    - data/processed/model.pkl (from T026)
    - data/processed/analysis/shap_bootstrap_results.json (from T034a/T033a)
"""
import os
import sys
import json
import logging
import pickle
import gc
from pathlib import Path
from typing import Dict, Any, List, Optional, Set

# Ensure project root is in path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logging_config import get_logger, set_log_level
from utils.config import load_hyperparameters

# Configure logging
logger = get_logger("stability_report")
set_log_level(logging.INFO)

# Constants
JACCARD_THRESHOLD = 0.7
ANALYSIS_DIR = PROJECT_ROOT / "data" / "processed" / "analysis"
FAILED_REPORT_PATH = ANALYSIS_DIR / "stability_failed.json"
SUCCESS_REPORT_PATH = ANALYSIS_DIR / "stability_report.json"


def load_json(filepath: Path) -> Dict[str, Any]:
    """Load a JSON file."""
    if not filepath.exists():
        raise FileNotFoundError(f"Required file not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)


def calculate_jaccard_similarity(set_a: Set[int], set_b: Set[int]) -> float:
    """
    Calculate Jaccard similarity between two sets of indices.
    J(A, B) = |A ∩ B| / |A ∪ B|
    """
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    return intersection / union if union > 0 else 0.0


def verify_cluster_stability(bootstrap_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Verify stability of top feature clusters across bootstrap resamples.

    Args:
        bootstrap_results: Dictionary containing bootstrap resample results.
                           Expected structure:
                           {
                               "resamples": [
                                   {
                                       "top_cluster_indices": [list of feature indices],
                                       "cluster_id": int,
                                       ...
                                   },
                                   ...
                               ],
                               "cluster_mapping": {cluster_id: [feature_indices]}
                           }

    Returns:
        Dictionary containing stability metrics and pass/fail status.
    """
    resamples = bootstrap_results.get("resamples", [])
    if len(resamples) < 2:
        raise ValueError("Insufficient bootstrap resamples for stability analysis.")

    # Extract top cluster indices from each resample
    top_cluster_sets = []
    for resample in resamples:
        indices = resample.get("top_cluster_indices", [])
        if indices:
            top_cluster_sets.append(set(indices))

    if len(top_cluster_sets) < 2:
        raise ValueError("Could not extract top cluster indices from resamples.")

    # Calculate pairwise Jaccard similarities
    jaccard_scores = []
    for i in range(len(top_cluster_sets)):
        for j in range(i + 1, len(top_cluster_sets)):
            score = calculate_jaccard_similarity(top_cluster_sets[i], top_cluster_sets[j])
            jaccard_scores.append(score)

    if not jaccard_scores:
        raise ValueError("No valid Jaccard scores computed.")

    avg_jaccard = sum(jaccard_scores) / len(jaccard_scores)
    min_jaccard = min(jaccard_scores)
    max_jaccard = max(jaccard_scores)

    return {
        "average_jaccard": avg_jaccard,
        "min_jaccard": min_jaccard,
        "max_jaccard": max_jaccard,
        "num_resamples": len(resamples),
        "num_comparisons": len(jaccard_scores),
        "threshold": JACCARD_THRESHOLD,
        "passed": avg_jaccard >= JACCARD_THRESHOLD
    }


def write_failed_report(stability_metrics: Dict[str, Any], output_path: Path) -> None:
    """
    Write a failure report to JSON and log a CRITICAL error.

    Args:
        stability_metrics: The computed stability metrics.
        output_path: Path to write the failure report.
    """
    report = {
        "status": "failed",
        "reason": "Jaccard similarity below threshold",
        "metrics": stability_metrics,
        "threshold": JACCARD_THRESHOLD,
        "action": "CI_FAILURE_TRIGGERED"
    }

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.critical(
        f"STABILITY CHECK FAILED: Average Jaccard={stability_metrics['average_jaccard']:.4f} "
        f"(< {JACCARD_THRESHOLD}). Report written to {output_path}. Exiting with code 1."
    )


def write_success_report(stability_metrics: Dict[str, Any], output_path: Path) -> None:
    """
    Write a success report to JSON.

    Args:
        stability_metrics: The computed stability metrics.
        output_path: Path to write the success report.
    """
    report = {
        "status": "passed",
        "metrics": stability_metrics,
        "threshold": JACCARD_THRESHOLD,
        "message": "Feature clusters are stable across bootstrap resamples."
    }

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(
        f"STABILITY CHECK PASSED: Average Jaccard={stability_metrics['average_jaccard']:.4f} "
        f"(>= {JACCARD_THRESHOLD}). Report written to {output_path}."
    )


def main() -> int:
    """
    Main entry point for generating the stability report.

    Returns:
        int: Exit code (0 for success, 1 for failure).
    """
    # Ensure analysis directory exists
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

    # Load bootstrap results from T033a/T034a
    bootstrap_file = ANALYSIS_DIR / "shap_bootstrap_results.json"
    if not bootstrap_file.exists():
        logger.error(f"Bootstrap results file not found: {bootstrap_file}")
        logger.error("Ensure T033a and T034a have been completed successfully.")
        return 1

    try:
        bootstrap_results = load_json(bootstrap_file)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(f"Failed to load bootstrap results: {e}")
        return 1

    # Verify cluster stability
    try:
        stability_metrics = verify_cluster_stability(bootstrap_results)
    except ValueError as e:
        logger.error(f"Stability verification failed: {e}")
        return 1

    # Check against threshold and handle accordingly
    if not stability_metrics["passed"]:
        write_failed_report(stability_metrics, FAILED_REPORT_PATH)
        return 1
    else:
        write_success_report(stability_metrics, SUCCESS_REPORT_PATH)
        return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

"""
Stability Report Generation for Molecular Polarity Prediction.

This module generates a comprehensive stability report verifying Jaccard similarity
metrics for both cluster and individual feature stability across bootstrap resamples.

It reads analysis artifacts produced by `models.stability_analysis` and `models.interpret`,
calculates the required metrics, and logs the results against the spec threshold (>= 0.7).
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.logging_config import get_logger, set_log_level
from models.stability_analysis import calculate_jaccard_similarity

# Constants
JACCARD_THRESHOLD = 0.7
ANALYSIS_DIR = Path("data/processed/analysis")
REPORT_PATH = ANALYSIS_DIR / "stability_report.json"
LOG_PATH = Path("logs/app.log")

def load_bootstrap_results(
    cluster_results_path: Path, 
    individual_results_path: Path
) -> Dict[str, Any]:
    """
    Load bootstrap analysis results from JSON files.
    
    Args:
        cluster_results_path: Path to cluster stability JSON (from T034a)
        individual_results_path: Path to individual feature stability JSON (from T034b)
        
    Returns:
        Dictionary containing loaded results or empty dicts if files missing.
    """
    results = {
        "cluster": {},
        "individual": {}
    }
    
    if cluster_results_path.exists():
        try:
            with open(cluster_results_path, 'r') as f:
                results["cluster"] = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logging.warning(f"Could not load cluster results: {e}")
    else:
        logging.warning(f"Cluster results file not found: {cluster_results_path}")
        
    if individual_results_path.exists():
        try:
            with open(individual_results_path, 'r') as f:
                results["individual"] = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logging.warning(f"Could not load individual results: {e}")
    else:
        logging.warning(f"Individual results file not found: {individual_results_path}")
        
    return results

def generate_stability_report(
    cluster_results: Dict[str, Any],
    individual_results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate the stability report with Jaccard similarity metrics.
    
    Args:
        cluster_results: Results from cluster stability analysis
        individual_results: Results from individual feature stability analysis
        
    Returns:
        Dictionary containing the full stability report.
    """
    report = {
        "threshold": JACCARD_THRESHOLD,
        "metrics": {},
        "status": "unknown",
        "details": {}
    }
    
    # Calculate Cluster Jaccard Similarity
    cluster_jaccard = 0.0
    if cluster_results and "jaccard_scores" in cluster_results:
        scores = cluster_results["jaccard_scores"]
        if isinstance(scores, list) and len(scores) > 0:
            cluster_jaccard = sum(scores) / len(scores)
        elif isinstance(scores, (int, float)):
            cluster_jaccard = float(scores)
    
    report["metrics"]["cluster_jaccard_mean"] = cluster_jaccard
    report["metrics"]["cluster_jaccard_pass"] = cluster_jaccard >= JACCARD_THRESHOLD
    report["details"]["cluster"] = {
        "raw_scores": cluster_results.get("jaccard_scores", []),
        "count": len(cluster_results.get("jaccard_scores", [])),
        "threshold_met": report["metrics"]["cluster_jaccard_pass"]
    }
    
    # Calculate Individual Jaccard Similarity
    individual_jaccard = 0.0
    if individual_results and "jaccard_scores" in individual_results:
        scores = individual_results["jaccard_scores"]
        if isinstance(scores, list) and len(scores) > 0:
            individual_jaccard = sum(scores) / len(scores)
        elif isinstance(scores, (int, float)):
            individual_jaccard = float(scores)
    
    report["metrics"]["individual_jaccard_mean"] = individual_jaccard
    report["metrics"]["individual_jaccard_pass"] = individual_jaccard >= JACCARD_THRESHOLD
    report["details"]["individual"] = {
        "raw_scores": individual_results.get("jaccard_scores", []),
        "count": len(individual_results.get("jaccard_scores", [])),
        "threshold_met": report["metrics"]["individual_jaccard_pass"]
    }
    
    # Determine Overall Status
    cluster_pass = report["metrics"]["cluster_jaccard_pass"]
    individual_pass = report["metrics"]["individual_jaccard_pass"]
    
    if cluster_pass and individual_pass:
        report["status"] = "PASS"
        logging.info(f"Stability Report: PASS (Cluster: {cluster_jaccard:.4f}, Individual: {individual_jaccard:.4f})")
    else:
        report["status"] = "FAIL"
        reason_parts = []
        if not cluster_pass:
            reason_parts.append(f"Cluster Jaccard ({cluster_jaccard:.4f}) < {JACCARD_THRESHOLD}")
        if not individual_pass:
            reason_parts.append(f"Individual Jaccard ({individual_jaccard:.4f}) < {JACCARD_THRESHOLD}")
        
        fail_msg = f"Stability Report: FAIL - {'; '.join(reason_parts)}"
        logging.warning(fail_msg)
        
        # Log specific failure as per task requirement
        if not cluster_pass:
            logging.warning(f"Cluster stability failed: Jaccard {cluster_jaccard:.4f} is below threshold {JACCARD_THRESHOLD}")
        if not individual_pass:
            logging.warning(f"Individual stability failed: Jaccard {individual_jaccard:.4f} is below threshold {JACCARD_THRESHOLD}")
    
    return report

def save_report(report: Dict[str, Any], output_path: Path) -> None:
    """
    Save the stability report to a JSON file.
    
    Args:
        report: The stability report dictionary.
        output_path: Path to save the JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logging.info(f"Stability report saved to: {output_path}")

def main():
    """Main entry point for generating the stability report."""
    # Setup logging
    logger = get_logger(__name__)
    set_log_level(logging.INFO)
    
    logger.info("Starting Stability Report Generation (T035)")
    
    # Define paths
    cluster_results_path = ANALYSIS_DIR / "cluster_stability_results.json"
    individual_results_path = ANALYSIS_DIR / "individual_stability_results.json"
    
    # Load results from previous tasks (T034a, T034b)
    results = load_bootstrap_results(cluster_results_path, individual_results_path)
    
    # Check if we have enough data to generate a report
    if not results["cluster"] and not results["individual"]:
        logger.error("No bootstrap results found. Cannot generate stability report.")
        # Create a failure report anyway
        report = {
            "threshold": JACCARD_THRESHOLD,
            "metrics": {
                "cluster_jaccard_mean": 0.0,
                "cluster_jaccard_pass": False,
                "individual_jaccard_mean": 0.0,
                "individual_jaccard_pass": False
            },
            "status": "FAIL",
            "details": {
                "cluster": {"error": "No data found"},
                "individual": {"error": "No data found"}
            },
            "reason": "Missing bootstrap analysis results from T034a/T034b"
        }
        save_report(report, REPORT_PATH)
        return 1
    
    # Generate report
    report = generate_stability_report(results["cluster"], results["individual"])
    
    # Save report
    save_report(report, REPORT_PATH)
    
    # Return exit code based on status
    return 0 if report["status"] == "PASS" else 1

if __name__ == "__main__":
    sys.exit(main())
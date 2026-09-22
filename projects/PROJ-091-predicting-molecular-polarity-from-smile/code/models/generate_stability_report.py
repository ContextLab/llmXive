import os
import sys
import json
import logging
import pickle
import gc
from pathlib import Path
from typing import Dict, Any, List, Optional

import numpy as np
import pandas as pd

# Import from stability_analysis module
from models.stability_analysis import (
    run_stability_analysis,
    calculate_jaccard_similarity
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_json(path: str) -> Dict[str, Any]:
    """Load a JSON file."""
    with open(path, 'r') as f:
        return json.load(f)

def calculate_jaccard_similarity(set_a: set, set_b: set) -> float:
    """Calculate Jaccard similarity between two sets."""
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    if union == 0:
        return 0.0
    return intersection / union

def verify_cluster_stability(
    stability_results: Dict[str, Any],
    threshold: float = 0.7
) -> bool:
    """
    Verify that the stability analysis passed the threshold.
    """
    mean_jaccard = stability_results.get('mean_jaccard_similarity', 0.0)
    return mean_jaccard >= threshold

def write_failed_report(output_path: str, results: Dict[str, Any]) -> None:
    """Write a failure report to disk."""
    report = {
        "status": "failed",
        "reason": "Jaccard similarity below threshold",
        "details": results
    }
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.error(f"Stability check FAILED. Report written to {output_path}")

def write_success_report(output_path: str, results: Dict[str, Any]) -> None:
    """Write a success report to disk."""
    report = {
        "status": "success",
        "message": "Cluster stability verified",
        "details": results
    }
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Stability check PASSED. Report written to {output_path}")

def main():
    """
    CLI entry point to generate stability report.
    This script orchestrates the stability analysis and generates the final report.
    
    Expected arguments:
    --shap-values: Path to SHAP values pickle file
    --clusters: Path to cluster_map.csv
    --output-json: Path to output JSON report (intermediate)
    --output-report: Path to final stability report (stability_report.md or .json)
    --n-bootstrap: Number of bootstrap resamples
    --top-k: Number of top clusters
    """
    import argparse

    parser = argparse.ArgumentParser(description="Generate stability report")
    parser.add_argument("--shap-values", required=True, help="Path to SHAP values pickle")
    parser.add_argument("--clusters", required=True, help="Path to cluster_map.csv")
    parser.add_argument("--output-json", required=True, help="Path to intermediate JSON results")
    parser.add_argument("--output-report", required=True, help="Path to final report file")
    parser.add_argument("--n-bootstrap", type=int, default=100)
    parser.add_argument("--top-k", type=int, default=10)

    args = parser.parse_args()

    try:
        # Run the stability analysis
        logger.info("Running stability analysis...")
        run_stability_analysis(
            shap_values_path=args.shap_values,
            cluster_map_path=args.clusters,
            output_path=args.output_json,
            n_bootstrap=args.n_bootstrap,
            top_k_clusters=args.top_k
        )

        # Load results
        with open(args.output_json, 'r') as f:
            results = json.load(f)

        # Verify threshold
        passed = verify_cluster_stability(results, threshold=0.7)

        # Generate final report
        if passed:
            write_success_report(args.output_report, results)
            logger.info("Stability check passed. Exiting with code 0.")
            sys.exit(0)
        else:
            write_failed_report(args.output_report, results)
            logger.critical("Stability check FAILED. Exiting with code 1.")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Failed to generate stability report: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

"""
Metrics Aggregator for Generalization Analysis.

Combines intra-family baseline metrics (T020a) and inter-family generalization
results (T021a) into a unified report for the project's success criteria.

This script reads existing JSON artifacts produced by upstream tasks and
aggregates them into a single `data/results/generalization_metrics.json`.
"""

import os
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

# Local imports matching the project API surface
from model.generalization_test import load_json as load_generalization_json
from model.baseline_metrics import BaselineReport

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents."""
    if not file_path.exists():
        raise FileNotFoundError(f"Required input file not found: {file_path}")
    with open(file_path, 'r') as f:
        return json.load(f)

def save_json_file(file_path: Path, data: Dict[str, Any]) -> None:
    """Save data to a JSON file with pretty printing."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved aggregated metrics to: {file_path}")

def aggregate_metrics(
    intra_family_report: Optional[Dict[str, Any]],
    inter_family_report: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Combine intra-family and inter-family metrics into a single report.

    Args:
        intra_family_report: Results from T020a (baseline metrics).
        inter_family_report: Results from T021a (generalization test).

    Returns:
        A unified dictionary containing all metrics and metadata.
    """
    result = {
        "status": "complete",
        "intra_family_metrics": {},
        "inter_family_metrics": {},
        "disclaimer": "These results are ML interpolations of DFT data, not first-principles solutions.",
        "aggregated_at": None
    }

    # Process intra-family metrics
    if intra_family_report:
        result["intra_family_metrics"] = {
            "mape": intra_family_report.get("mape", None),
            "rmse": intra_family_report.get("rmse", None),
            "r2": intra_family_report.get("r2", None),
            "num_families": intra_family_report.get("num_families", 0)
        }
        logger.info(f"Loaded intra-family MAPE: {result['intra_family_metrics']['mape']}")
    else:
        logger.warning("No intra-family report found. Intra-family metrics will be null.")
        result["status"] = "incomplete"

    # Process inter-family metrics
    if inter_family_report:
        result["inter_family_metrics"] = {
            "mape": inter_family_report.get("inter_family_mape", None),
            "rmse": inter_family_report.get("inter_family_rmse", None),
            "r2": inter_family_report.get("inter_family_r2", None),
            "num_test_families": inter_family_report.get("num_test_families", 0),
            "family_disjoint_verified": inter_family_report.get("family_disjoint_verified", False)
        }
        logger.info(f"Loaded inter-family MAPE: {result['inter_family_metrics']['mape']}")
    else:
        logger.warning("No inter-family report found. Inter-family metrics will be null.")
        result["status"] = "incomplete"

    # Calculate delta if both are present
    if (result["intra_family_metrics"]["mape"] is not None and
        result["inter_family_metrics"]["mape"] is not None):
        intra_mape = result["intra_family_metrics"]["mape"]
        inter_mape = result["inter_family_metrics"]["mape"]
        result["generalization_drop"] = {
            "absolute": inter_mape - intra_mape,
            "relative_percent": ((inter_mape - intra_mape) / intra_mape * 100) if intra_mape != 0 else None
        }
        logger.info(f"Generalization drop (MAPE): {result['generalization_drop']['absolute']:.4f}")

    return result

def run_aggregation(
    intra_family_path: Path,
    inter_family_path: Path,
    output_path: Path
) -> Dict[str, Any]:
    """
    Main execution function to load, aggregate, and save metrics.

    Args:
        intra_family_path: Path to the intra-family baseline report (T020a).
        inter_family_path: Path to the inter-family generalization report (T021a).
        output_path: Path where the aggregated JSON will be written.

    Returns:
        The aggregated metrics dictionary.
    """
    logger.info(f"Starting metrics aggregation.")
    logger.info(f"  Intra-family source: {intra_family_path}")
    logger.info(f"  Inter-family source: {inter_family_path}")
    logger.info(f"  Output destination: {output_path}")

    # Load inputs
    intra_data = None
    if intra_family_path.exists():
        try:
            intra_data = load_json_file(intra_family_path)
        except Exception as e:
            logger.error(f"Failed to load intra-family report: {e}")
            intra_data = None
    else:
        logger.warning(f"Intra-family report not found at {intra_family_path}")

    inter_data = None
    if inter_family_path.exists():
        try:
            inter_data = load_json_file(inter_family_path)
        except Exception as e:
            logger.error(f"Failed to load inter-family report: {e}")
            inter_data = None
    else:
        logger.warning(f"Inter-family report not found at {inter_family_path}")

    # Aggregate
    aggregated = aggregate_metrics(intra_data, inter_data)

    # Save
    save_json_file(output_path, aggregated)

    return aggregated

def main():
    """CLI entry point for the metrics aggregator."""
    parser = argparse.ArgumentParser(
        description="Aggregate intra-family and inter-family metrics into a single report."
    )
    parser.add_argument(
        "--intra-family",
        type=Path,
        required=True,
        help="Path to the intra-family baseline metrics JSON (from T020a)."
    )
    parser.add_argument(
        "--inter-family",
        type=Path,
        required=True,
        help="Path to the inter-family generalization metrics JSON (from T021a)."
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Path to write the aggregated generalization_metrics.json."
    )

    args = parser.parse_args()

    try:
        run_aggregation(args.intra_family, args.inter_family, args.output)
        logger.info("Metrics aggregation completed successfully.")
    except Exception as e:
        logger.error(f"Metrics aggregation failed: {e}")
        raise

if __name__ == "__main__":
    main()
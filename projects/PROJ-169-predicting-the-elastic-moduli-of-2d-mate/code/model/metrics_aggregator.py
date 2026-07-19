"""
Metrics Aggregator for Generalization Analysis.

Combines intra-family baseline metrics (T020a) and inter-family generalization
metrics (T021a) into a unified report at `data/results/generalization_metrics.json`.
"""

import os
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_json_file(path: Path) -> Dict[str, Any]:
    """Load a JSON file, returning an empty dict if not found."""
    if not path.exists():
        logger.warning(f"File not found: {path}. Returning empty dict.")
        return {}
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON in {path}: {e}")
        return {}

def save_json_file(path: Path, data: Dict[str, Any]) -> None:
    """Save a dictionary to a JSON file with pretty printing."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved metrics to {path}")

def aggregate_metrics(
    baseline_metrics: Dict[str, Any],
    generalization_metrics: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Combine baseline and generalization results into a unified report.

    Args:
        baseline_metrics: Output from T020a (intra-family baseline).
        generalization_metrics: Output from T021a (inter-family test).

    Returns:
        Aggregated metrics dictionary.
    """
    logger.info("Aggregating baseline and generalization metrics...")

    # Extract specific values with defaults
    intra_mape = baseline_metrics.get('intra_family_mape')
    intra_rmse = baseline_metrics.get('intra_family_rmse')

    inter_mape = generalization_metrics.get('inter_family_mape')
    inter_rmse = generalization_metrics.get('inter_family_rmse')
    inter_r2 = generalization_metrics.get('inter_family_r2')

    # Calculate delta (performance drop)
    mape_delta = None
    if intra_mape is not None and inter_mape is not None:
        mape_delta = inter_mape - intra_mape
        logger.info(f"Inter-family MAPE delta: {mape_delta:.4f} (Intra: {intra_mape:.4f}, Inter: {inter_mape:.4f})")

    # Construct the unified report
    aggregated = {
        "status": "success",
        "intra_family_metrics": {
            "mape": intra_mape,
            "rmse": intra_rmse
        },
        "inter_family_metrics": {
            "mape": inter_mape,
            "rmse": inter_rmse,
            "r2": inter_r2
        },
        "generalization_delta": {
            "mape_delta": mape_delta,
            "description": "Difference between inter-family and intra-family MAPE"
        },
        "metadata": {
            "disclaimer": "These results are ML interpolations of DFT data, not first-principles solutions.",
            "source": "Aggregated from T020a (baseline) and T021a (generalization)"
        }
    }

    return aggregated

def run_aggregation(
    baseline_path: Optional[Path] = None,
    generalization_path: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run the aggregation pipeline.

    Args:
        baseline_path: Path to T020a output (default: data/results/baseline_metrics.json).
        generalization_path: Path to T021a output (default: data/results/generalization_metrics.json).
        output_path: Path to write the aggregated result (default: data/results/generalization_metrics.json).

    Returns:
        The aggregated metrics dictionary.
    """
    # Default paths
    if baseline_path is None:
        baseline_path = Path("data/results/baseline_metrics.json")
    if generalization_path is None:
        generalization_path = Path("data/results/generalization_metrics.json")
    if output_path is None:
        output_path = Path("data/results/generalization_metrics.json")

    # Load inputs
    baseline_data = load_json_file(baseline_path)
    generalization_data = load_json_file(generalization_path)

    # Check if we have valid data to aggregate
    if not baseline_data and not generalization_data:
        logger.error("No valid input data found. Cannot aggregate.")
        # Return a failure state
        aggregated = {
            "status": "failed",
            "error": "No valid input data found",
            "metadata": {
                "disclaimer": "These results are ML interpolations of DFT data, not first-principles solutions."
            }
        }
    else:
        aggregated = aggregate_metrics(baseline_data, generalization_data)

    # Save result
    save_json_file(output_path, aggregated)

    return aggregated

def main():
    parser = argparse.ArgumentParser(description="Aggregate generalization metrics.")
    parser.add_argument(
        "--baseline",
        type=Path,
        default=Path("data/results/baseline_metrics.json"),
        help="Path to intra-family baseline metrics (T020a output)."
    )
    parser.add_argument(
        "--generalization",
        type=Path,
        default=Path("data/results/generalization_metrics.json"),
        help="Path to inter-family generalization metrics (T021a output)."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/results/generalization_metrics.json"),
        help="Path to write the aggregated metrics."
    )

    args = parser.parse_args()

    logger.info(f"Loading baseline from: {args.baseline}")
    logger.info(f"Loading generalization from: {args.generalization}")
    logger.info(f"Output will be written to: {args.output}")

    result = run_aggregation(
        baseline_path=args.baseline,
        generalization_path=args.generalization,
        output_path=args.output
    )

    if result.get("status") == "success":
        logger.info("Aggregation completed successfully.")
    else:
        logger.warning("Aggregation completed with warnings or errors.")

    return 0 if result.get("status") == "success" else 1

if __name__ == "__main__":
    exit(main())
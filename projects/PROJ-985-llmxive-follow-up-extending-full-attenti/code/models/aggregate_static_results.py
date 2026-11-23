import os
import json
import logging
import argparse
from typing import Dict, Any, List, Optional
import numpy as np

from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent.parent

def load_eval_scores(input_path: str) -> List[Dict[str, Any]]:
    """
    Load per-document evaluation scores from a JSON file.

    Args:
        input_path: Path to the JSON file containing per-document scores.

    Returns:
        List of dictionaries containing document scores.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"Expected a list of document scores, got {type(data)}")

    logger.info(f"Loaded {len(data)} document scores from {input_path}")
    return data

def aggregate_metrics(scores: List[Dict[str, Any]], metric_name: str = "perplexity") -> Dict[str, Any]:
    """
    Compute mean, standard deviation, and variance for a specific metric
    across all documents.

    Args:
        scores: List of document score dictionaries.
        metric_name: The key in each score dict to aggregate (default: "perplexity").

    Returns:
        Dictionary with mean, std, and variance for the metric.
    """
    if not scores:
        raise ValueError("No scores provided for aggregation")

    # Extract values for the specific metric
    values = []
    for doc_score in scores:
        if metric_name not in doc_score:
            logger.warning(f"Metric '{metric_name}' not found in document {doc_score.get('document_id', 'unknown')}, skipping")
            continue
        val = doc_score[metric_name]
        if isinstance(val, (int, float)) and not np.isnan(val):
            values.append(float(val))

    if not values:
        raise ValueError(f"No valid values found for metric '{metric_name}'")

    values_np = np.array(values)
    mean_val = float(np.mean(values_np))
    std_val = float(np.std(values_np))
    var_val = float(np.var(values_np))

    logger.info(f"Aggregated {metric_name}: mean={mean_val:.4f}, std={std_val:.4f}, var={var_val:.6f}")

    return {
        "mean_metric": mean_val,
        "std_metric": std_val,
        "variance_metric": var_val,
        "n_documents": len(values),
        "metric_name": metric_name
    }

def save_aggregated_results(
    aggregated_data: Dict[str, Any],
    output_path: str
) -> None:
    """
    Save aggregated results to a JSON file.

    Args:
        aggregated_data: Dictionary containing aggregated metrics.
        output_path: Path to the output JSON file.
    """
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(aggregated_data, f, indent=2)

    logger.info(f"Saved aggregated results to {output_path}")

def main():
    """
    Main entry point for aggregating static heuristic evaluation results.

    Reads per-document scores from T027 output, computes mean and variance
    for perplexity and exact_match, and saves to data/results/static_eval_aggregated.json.
    """
    parser = argparse.ArgumentParser(
        description="Aggregate static heuristic evaluation results"
    )
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to per-document scores JSON (default: auto-detect from project structure)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to output aggregated JSON (default: auto-detect from project structure)"
    )
    parser.add_argument(
        "--metrics",
        type=str,
        nargs="+",
        default=["perplexity", "exact_match"],
        help="Metrics to aggregate (default: perplexity exact_match)"
    )

    args = parser.parse_args()

    project_root = get_project_root()

    # Default input path (from T027)
    if args.input is None:
        input_path = project_root / "data" / "intermediate" / "static_per_document.json"
    else:
        input_path = Path(args.input)

    # Default output path
    if args.output is None:
        output_path = project_root / "data" / "results" / "static_eval_aggregated.json"
    else:
        output_path = Path(args.output)

    logger.info(f"Input path: {input_path}")
    logger.info(f"Output path: {output_path}")

    try:
        # Load per-document scores
        scores = load_eval_scores(str(input_path))

        # Aggregate metrics
        aggregated_results = {
            "n_documents": len(scores),
            "metrics": {}
        }

        for metric in args.metrics:
            try:
                metric_agg = aggregate_metrics(scores, metric_name=metric)
                aggregated_results["metrics"][metric] = metric_agg
            except ValueError as e:
                logger.error(f"Failed to aggregate {metric}: {e}")
                aggregated_results["metrics"][metric] = {"error": str(e)}

        # Save results
        save_aggregated_results(aggregated_results, str(output_path))

        logger.info("Aggregation completed successfully")
        return 0

    except Exception as e:
        logger.error(f"Aggregation failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit(main())

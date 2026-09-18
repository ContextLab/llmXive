"""
Aggregation logic for static model evaluation scores.

Computes mean and variance of evaluation metrics across multiple seeds
and saves the aggregated results to data/results/static_aggregated.json.
"""
import os
import json
import logging
import argparse
from typing import Dict, Any, List, Optional

import numpy as np

logger = logging.getLogger(__name__)

# Paths
INPUT_DIR = "data/intermediate/static_eval_scores.json"
OUTPUT_DIR = "data/results/static_aggregated.json"
SEEDS_DIR = "data/intermediate/models/seeds"


def load_eval_scores() -> Dict[str, Any]:
    """
    Load the evaluation scores from the static_eval_scores.json file.
    Expected format: { "seeds": [ { "seed": int, "metrics": { ... } }, ... ] }
    """
    if not os.path.exists(INPUT_DIR):
        raise FileNotFoundError(
            f"Input file not found: {INPUT_DIR}. "
            "Ensure T019b (evaluate_static.py) has been run successfully."
        )

    with open(INPUT_DIR, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "seeds" not in data:
        raise ValueError(
            f"Invalid format in {INPUT_DIR}. Expected a 'seeds' key."
        )

    return data


def aggregate_metrics(eval_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute mean and variance of metrics across all seeds.

    Returns:
        Dict with keys: mean_metric, std_metric, n_seeds, seed_values
    """
    seeds = eval_data["seeds"]
    if not seeds:
        raise ValueError("No seed results found to aggregate.")

    # Assume all seeds have the same metric keys
    # We aggregate 'accuracy', 'precision', 'recall', 'f1' by default
    metric_keys = ["accuracy", "precision", "recall", "f1"]
    
    aggregated: Dict[str, Any] = {
        "n_seeds": len(seeds),
        "seed_values": [],
        "metrics": {}
    }

    for key in metric_keys:
        values = []
        for seed_entry in seeds:
            metrics = seed_entry.get("metrics", {})
            if key in metrics:
                values.append(metrics[key])
            else:
                logger.warning(f"Metric '{key}' not found in seed {seed_entry.get('seed')}. Skipping.")

        if not values:
            logger.warning(f"No values found for metric '{key}'. Skipping aggregation.")
            continue

        values_arr = np.array(values)
        aggregated["metrics"][f"mean_{key}"] = float(np.mean(values_arr))
        aggregated["metrics"][f"std_{key}"] = float(np.std(values_arr))
        
        # Store individual seed values for reference
        aggregated["seed_values"].append({
            "metric": key,
            "values": values
        })

    return aggregated


def save_aggregated_results(aggregated: Dict[str, Any], output_path: str) -> None:
    """Save the aggregated results to a JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(aggregated, f, indent=2)
    logger.info(f"Aggregated results saved to {output_path}")


def main(args: Optional[argparse.Namespace] = None) -> None:
    """Main entry point for aggregation."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    if args is None:
        parser = argparse.ArgumentParser(description="Aggregate static model evaluation scores.")
        parser.add_argument(
            "--input",
            type=str,
            default=INPUT_DIR,
            help="Path to input evaluation scores JSON."
        )
        parser.add_argument(
            "--output",
            type=str,
            default=OUTPUT_DIR,
            help="Path to output aggregated results JSON."
        )
        args = parser.parse_args()

    logger.info(f"Loading evaluation scores from {args.input}")
    eval_data = load_eval_scores()

    logger.info("Aggregating metrics across seeds...")
    aggregated = aggregate_metrics(eval_data)

    logger.info(f"Saving aggregated results to {args.output}")
    save_aggregated_results(aggregated, args.output)

    logger.info("Aggregation complete.")


if __name__ == "__main__":
    main()

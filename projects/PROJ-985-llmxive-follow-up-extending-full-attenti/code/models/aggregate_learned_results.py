import os
import json
import logging
import argparse
from typing import Dict, Any, List, Optional
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_eval_scores(base_dir: str = "data/intermediate/baseline_seeds") -> List[Dict[str, Any]]:
    """
    Load all evaluation score JSON files from the baseline seeds directory.
    
    Args:
        base_dir: Directory containing seed result files (e.g., seed_0.json, seed_1.json)
        
    Returns:
        List of dictionaries containing evaluation metrics for each seed.
        
    Raises:
        FileNotFoundError: If no score files are found in the directory.
    """
    score_files = []
    
    if not os.path.exists(base_dir):
        raise FileNotFoundError(f"Baseline seeds directory not found: {base_dir}")
    
    for filename in sorted(os.listdir(base_dir)):
        if filename.startswith("seed_") and filename.endswith(".json"):
            score_files.append(os.path.join(base_dir, filename))
    
    if not score_files:
        raise FileNotFoundError(f"No seed result files found in {base_dir}")
    
    logger.info(f"Found {len(score_files)} seed result files in {base_dir}")
    
    scores = []
    for filepath in score_files:
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                scores.append(data)
                logger.info(f"Loaded scores from {filepath}: {data.get('seed', 'unknown')}")
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load {filepath}: {e}")
            raise
    
    return scores

def aggregate_metrics(scores: List[Dict[str, Any]], metric_name: str = "exact_match") -> Dict[str, Any]:
    """
    Compute mean and variance of a specific metric across all seeds.
    
    Args:
        scores: List of evaluation score dictionaries from each seed.
        metric_name: The key in each score dict to aggregate (default: "exact_match").
        
    Returns:
        Dictionary with aggregated metrics:
        {
            "mean_metric": float,
            "std_metric": float,
            "n_seeds": int,
            "seed_values": List[float]
        }
    """
    if not scores:
        raise ValueError("No scores provided for aggregation")
    
    values = []
    for i, score in enumerate(scores):
        if metric_name not in score:
            raise KeyError(f"Metric '{metric_name}' not found in seed {i} results")
        val = score[metric_name]
        if not isinstance(val, (int, float)):
            raise TypeError(f"Metric '{metric_name}' in seed {i} is not numeric: {type(val)}")
        values.append(float(val))
    
    values_array = np.array(values)
    mean_val = float(np.mean(values_array))
    std_val = float(np.std(values_array))
    
    return {
        "mean_metric": mean_val,
        "std_metric": std_val,
        "n_seeds": len(values),
        "seed_values": values
    }

def save_aggregated_results(
    aggregated_data: Dict[str, Any],
    output_path: str = "data/results/baseline_aggregated.json"
) -> None:
    """
    Save aggregated results to a JSON file.
    
    Args:
        aggregated_data: Dictionary containing aggregated metrics.
        output_path: Path to save the JSON output.
    """
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(aggregated_data, f, indent=2)
    
    logger.info(f"Saved aggregated results to {output_path}")

def main():
    """
    Main entry point for aggregating learned baseline results.
    
    Reads individual seed evaluation results from data/intermediate/baseline_seeds/,
    computes mean and variance for exact_match and perplexity, and saves
    the aggregated results to data/results/baseline_aggregated.json.
    """
    parser = argparse.ArgumentParser(
        description="Aggregate learned baseline (RTPurbo) evaluation results across seeds."
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default="data/intermediate/baseline_seeds",
        help="Directory containing seed result JSON files (default: data/intermediate/baseline_seeds)"
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default="data/results/baseline_aggregated.json",
        help="Path to save aggregated results (default: data/results/baseline_aggregated.json)"
    )
    parser.add_argument(
        "--metrics",
        type=str,
        nargs="+",
        default=["exact_match", "perplexity"],
        help="Metrics to aggregate (default: exact_match perplexity)"
    )
    
    args = parser.parse_args()
    
    try:
        logger.info(f"Loading evaluation scores from {args.input_dir}")
        scores = load_eval_scores(args.input_dir)
        
        if not scores:
            logger.error("No evaluation scores found. Cannot aggregate.")
            return 1
        
        # Aggregate each requested metric
        aggregated_results = {
            "n_seeds": len(scores),
            "metrics": {}
        }
        
        for metric in args.metrics:
            logger.info(f"Aggregating metric: {metric}")
            metric_agg = aggregate_metrics(scores, metric_name=metric)
            aggregated_results["metrics"][metric] = metric_agg
            logger.info(f"  Mean: {metric_agg['mean_metric']:.4f}, Std: {metric_agg['std_metric']:.4f}")
        
        # Save results
        save_aggregated_results(aggregated_results, args.output_path)
        
        logger.info("Aggregation completed successfully.")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except (KeyError, TypeError, ValueError) as e:
        logger.error(f"Data processing error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
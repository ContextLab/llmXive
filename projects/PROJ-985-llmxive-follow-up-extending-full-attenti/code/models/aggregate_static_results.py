"""
Aggregation logic for static evaluation scores.

Reads per-seed evaluation results from data/intermediate/static_eval_scores.json,
computes mean and variance (standard deviation) for each metric, and saves
the aggregated results to data/results/static_aggregated.json.

Schema:
{
    "mean_perplexity": float,
    "std_perplexity": float,
    "mean_exact_match": float,
    "std_exact_match": float,
    "n_seeds": int,
    "seed_values": [
        {
            "seed": int,
            "perplexity": float,
            "exact_match": float
        },
        ...
    ]
}
"""
import os
import json
import logging
import argparse
from typing import Dict, Any, List, Optional
import numpy as np

# Ensure we can import from code/
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)

def load_eval_scores(input_path: str) -> Dict[str, Any]:
    """
    Load evaluation scores from a JSON file.
    
    Args:
        input_path: Path to the JSON file containing evaluation scores.
        
    Returns:
        Dictionary containing the evaluation scores.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Evaluation scores file not found: {input_path}")
    
    with open(input_path, 'r') as f:
        data = json.load(f)
        
    logger.info(f"Loaded evaluation scores from {input_path}")
    return data

def aggregate_metrics(eval_scores: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute mean and standard deviation for each metric across seeds.
    
    Args:
        eval_scores: Dictionary containing per-seed evaluation scores.
        
    Returns:
        Dictionary with aggregated metrics (mean, std, n_seeds, seed_values).
    """
    seed_values = eval_scores.get("seed_scores", [])
    
    if not seed_values:
        logger.warning("No seed scores found in input file.")
        return {
            "mean_perplexity": 0.0,
            "std_perplexity": 0.0,
            "mean_exact_match": 0.0,
            "std_exact_match": 0.0,
            "n_seeds": 0,
            "seed_values": []
        }
    
    perplexities = [s["perplexity"] for s in seed_values]
    exact_matches = [s["exact_match"] for s in seed_values]
    
    mean_perplexity = float(np.mean(perplexities))
    std_perplexity = float(np.std(perplexities))
    mean_exact_match = float(np.mean(exact_matches))
    std_exact_match = float(np.std(exact_matches))
    n_seeds = len(seed_values)
    
    aggregated = {
        "mean_perplexity": mean_perplexity,
        "std_perplexity": std_perplexity,
        "mean_exact_match": mean_exact_match,
        "std_exact_match": std_exact_match,
        "n_seeds": n_seeds,
        "seed_values": seed_values
    }
    
    logger.info(f"Aggregated metrics for {n_seeds} seeds")
    logger.info(f"  Perplexity: mean={mean_perplexity:.4f}, std={std_perplexity:.4f}")
    logger.info(f"  Exact Match: mean={mean_exact_match:.4f}, std={std_exact_match:.4f}")
    
    return aggregated

def save_aggregated_results(aggregated: Dict[str, Any], output_path: str) -> None:
    """
    Save aggregated results to a JSON file.
    
    Args:
        aggregated: Dictionary containing aggregated metrics.
        output_path: Path to the output JSON file.
    """
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(aggregated, f, indent=2)
        
    logger.info(f"Saved aggregated results to {output_path}")

def main():
    """Main entry point for the aggregation script."""
    parser = argparse.ArgumentParser(description="Aggregate static evaluation scores")
    parser.add_argument(
        "--input",
        type=str,
        default="data/intermediate/static_eval_scores.json",
        help="Path to the input evaluation scores JSON file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/results/static_aggregated.json",
        help="Path to the output aggregated results JSON file"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Load evaluation scores
        eval_scores = load_eval_scores(args.input)
        
        # Aggregate metrics
        aggregated = aggregate_metrics(eval_scores)
        
        # Save results
        save_aggregated_results(aggregated, args.output)
        
        logger.info("Aggregation completed successfully")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in input file: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during aggregation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

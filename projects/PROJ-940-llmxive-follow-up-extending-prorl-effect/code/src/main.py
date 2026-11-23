import argparse
import json
import os
import logging
import sys
from typing import List, Dict, Any, Optional

# Import existing utilities and components
from src.config import get_config
from src.data_loader import load_sessions
from src.graph_builder import build_graph
from src.path_generator import (
    generate_greedy_paths,
    apply_src,
    apply_psa,
    apply_prorl_rectification
)
from src.evaluator import Evaluator, load_test_sessions, save_metrics_to_json
from src.exceptions import DataFetchError, GraphDisconnectionError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_paths_from_json(filepath: str) -> List[Dict[str, Any]]:
    """Load paths from a JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Paths file not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def save_paths_to_json(paths: List[Dict[str, Any]], filepath: str) -> None:
    """Save paths to a JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(paths, f, indent=2)
    logger.info(f"Saved {len(paths)} paths to {filepath}")

def validate_schema(data: Dict[str, Any], expected_keys: List[str]) -> bool:
    """Validate that data contains expected keys."""
    missing = [k for k in expected_keys if k not in data]
    if missing:
        logger.error(f"Schema validation failed. Missing keys: {missing}")
        return False
    return True

def validate_sc005(greedy_paths: List[Dict[str, Any]], rectified_paths: List[Dict[str, Any]], threshold: float = 0.01) -> Dict[str, Any]:
    """
    Implement SC-005: Verify mean absolute difference between rectified and raw scores >= 0.01 for Greedy paths only.
    
    Args:
        greedy_paths: List of path dictionaries with 'score' key (raw greedy scores)
        rectified_paths: List of path dictionaries with 'score' key (ProRL rectified scores)
        threshold: Minimum required mean absolute difference (default 0.01)
    
    Returns:
        Dict with status ('pass'/'fail'), calculated value, and threshold
    """
    if len(greedy_paths) != len(rectified_paths):
        raise ValueError(f"Path count mismatch: {len(greedy_paths)} greedy vs {len(rectified_paths)} rectified")
    
    if len(greedy_paths) == 0:
        logger.warning("No paths to evaluate for SC-005. Returning fail.")
        return {
            "status": "fail",
            "value": 0.0,
            "threshold": threshold
        }
    
    raw_scores = [p.get('score', 0.0) for p in greedy_paths]
    rectified_scores = [p.get('score', 0.0) for p in rectified_paths]
    
    abs_diffs = [abs(r - g) for r, g in zip(rectified_scores, raw_scores)]
    mean_abs_diff = sum(abs_diffs) / len(abs_diffs)
    
    status = "pass" if mean_abs_diff >= threshold else "fail"
    
    result = {
        "status": status,
        "value": float(mean_abs_diff),
        "threshold": float(threshold)
    }
    
    logger.info(f"SC-005 Check: Mean Abs Diff = {mean_abs_diff:.6f} (Threshold: {threshold}) -> {status.upper()}")
    return result

def generate_greedy_only_baseline(seed_item: str, graph: Dict, config: Dict) -> List[Dict[str, Any]]:
    """Generate greedy paths only (no beam search) for baseline comparison."""
    logger.info(f"Generating greedy-only baseline for seed: {seed_item}")
    paths = generate_greedy_paths(seed_item, graph, config)
    return paths

def run_evaluation_pipeline(seed_item: str, test_sessions: List[Dict], graph: Dict, config: Dict) -> Dict[str, Any]:
    """
    Run the full evaluation pipeline for a single seed item.
    Returns metrics and path data for SC-005 validation.
    """
    # 1. Generate Greedy Paths (Raw)
    greedy_paths = generate_greedy_only_baseline(seed_item, graph, config)
    if not greedy_paths:
        logger.warning(f"No greedy paths generated for seed {seed_item}")
        return {"paths": [], "metrics": {}, "sc005_data": None}
    
    # 2. Apply ProRL Rectification (SRC + PSA)
    # Apply SRC
    rectified_paths = apply_src(greedy_paths, config)
    # Apply PSA
    rectified_paths = apply_psa(rectified_paths, config)
    
    # 3. Evaluate against ground truth
    evaluator = Evaluator(test_sessions)
    metrics = evaluator.evaluate_paths(rectified_paths, seed_item)
    
    return {
        "paths": {
            "greedy": greedy_paths,
            "rectified": rectified_paths
        },
        "metrics": metrics,
        "sc005_data": {
            "greedy_scores": [p['score'] for p in greedy_paths],
            "rectified_scores": [p['score'] for p in rectified_paths]
        }
    }

def main():
    parser = argparse.ArgumentParser(description="llmXive ProRL Pipeline")
    parser.add_argument("--dataset", type=str, default="ml-latest-small", help="Dataset to use")
    parser.add_argument("--seed", type=str, default="123", help="Seed item ID")
    parser.add_argument("--config", type=str, default="config.yaml", help="Config file path")
    args = parser.parse_args()

    config = get_config(args.config)
    
    # Load Data
    try:
        logger.info(f"Loading sessions from {args.dataset}...")
        sessions = load_sessions(args.dataset, streaming=True)
    except DataFetchError as e:
        logger.error(f"Failed to load data: {e}")
        sys.exit(1)

    # Build Graph
    logger.info("Building similarity graph...")
    graph = build_graph(sessions, config)

    # Load Test Sessions
    test_sessions = load_test_sessions(sessions)

    # Run Evaluation
    results = run_evaluation_pipeline(args.seed, test_sessions, graph, config)

    # Save Intermediate Results
    os.makedirs("results", exist_ok=True)
    
    # Save Greedy Paths
    greedy_paths = results["paths"]["greedy"]
    save_paths_to_json(greedy_paths, "results/greedy_paths.json")

    # Save Rectified Paths
    rectified_paths = results["paths"]["rectified"]
    save_paths_to_json(rectified_paths, "results/greedy_rectified_paths.json")

    # SC-005 Validation
    if results["sc005_data"]:
        sc005_result = validate_sc005(
            results["sc005_data"]["greedy_scores"],
            results["sc005_data"]["rectified_scores"]
        )
        with open("results/sc005_status.json", 'w') as f:
            json.dump(sc005_result, f, indent=2)
        logger.info(f"SC-005 Status written to results/sc005_status.json")
    else:
        logger.warning("SC-005 data not available. Skipping validation.")

    # Save Metrics
    if results["metrics"]:
        save_metrics_to_json(results["metrics"], "results/metrics_comparison.json")

    logger.info("Pipeline completed successfully.")

if __name__ == "__main__":
    main()
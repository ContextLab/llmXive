import argparse
import json
import os
import logging
import sys
from typing import List, Dict, Any, Optional

from src.config import get_config
from src.data_loader import load_dataset, split_test_sessions
from src.graph_builder import build_graph, get_connected_component
from src.path_generator import generate_greedy_paths, generate_beam_paths, apply_prorl_rectification
from src.evaluator import load_test_sessions, save_metrics_to_json, Evaluator
from src.exceptions import DataFetchError, GraphDisconnectionError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_paths_from_json(filepath: str) -> List[Dict[str, Any]]:
    """Load paths from a JSON file."""
    if not os.path.exists(filepath):
        logger.warning(f"File not found: {filepath}, returning empty list.")
        return []
    with open(filepath, 'r') as f:
        return json.load(f)

def save_paths_to_json(paths: List[Dict[str, Any]], filepath: str) -> None:
    """Save paths to a JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(paths, f, indent=2)
    logger.info(f"Saved {len(paths)} paths to {filepath}")

def run_evaluation_pipeline(
    dataset_name: str,
    seed_item_id: Optional[str] = None,
    k: int = 10
) -> None:
    """
    Run the full evaluation pipeline:
    1. Load data and build graph.
    2. Generate Greedy and Beam paths.
    3. Apply ProRL rectification.
    4. Evaluate against test set.
    5. Save results.
    """
    config = get_config()
    
    # 1. Load Data
    logger.info(f"Loading dataset: {dataset_name}")
    try:
        data = load_dataset(dataset_name, streaming=False) # Load full for graph building if feasible, or stream logic adapted
        # Note: For large datasets, streaming logic in load_dataset should handle sampling as per T009a
        if data is None:
            raise DataFetchError(f"Failed to load dataset {dataset_name}")
    except Exception as e:
        logger.error(f"Data loading failed: {e}")
        raise

    # 2. Build Graph
    logger.info("Building similarity graph...")
    graph = build_graph(data, config)
    
    # 3. Generate Paths
    # If seed_item_id is provided, run for specific seed; else run for all test seeds
    seeds = [seed_item_id] if seed_item_id else [s['seed_id'] for s in load_test_sessions(dataset_name)]
    
    all_greedy_paths = []
    all_greedy_rectified = []
    all_beam_rectified = []

    for seed in seeds:
        if seed is None: continue
        logger.info(f"Processing seed: {seed}")
        
        # Greedy
        greedy_paths = generate_greedy_paths(seed, graph, config)
        all_greedy_paths.extend(greedy_paths)
        
        # Rectify Greedy
        rectified_greedy = apply_prorl_rectification(greedy_paths, config)
        all_greedy_rectified.extend(rectified_greedy)
        
        # Beam
        beam_paths = generate_beam_paths(seed, graph, config)
        rectified_beam = apply_prorl_rectification(beam_paths, config)
        all_beam_rectified.extend(rectified_beam)

    # 4. Save Raw and Rectified Paths
    base_results = "code/results"
    save_paths_to_json(all_greedy_paths, f"{base_results}/greedy_paths.json")
    save_paths_to_json(all_greedy_rectified, f"{base_results}/greedy_rectified_paths.json")
    save_paths_to_json(all_beam_rectified, f"{base_results}/beam_rectified_paths.json")

    # 5. Evaluate
    logger.info("Running evaluation against test set...")
    evaluator = Evaluator(dataset_name)
    metrics = evaluator.evaluate(all_greedy_paths, all_greedy_rectified, all_beam_rectified, k)
    save_metrics_to_json(metrics, f"{base_results}/evaluation_metrics.json")

def validate_sc005(
    raw_paths_file: str = "code/results/greedy_paths.json",
    rectified_paths_file: str = "code/results/greedy_rectified_paths.json",
    threshold: float = 0.01,
    output_file: str = "code/results/sc005_status.json"
) -> Dict[str, Any]:
    """
    Validates Specification SC-005:
    Verify that the mean absolute difference between rectified and raw scores is >= threshold.
    
    Writes the result to output_file.
    """
    logger.info(f"Validating SC-005: Comparing {raw_paths_file} vs {rectified_paths_file}")
    
    raw_paths = load_paths_from_json(raw_paths_file)
    rectified_paths = load_paths_from_json(rectified_paths_file)
    
    if not raw_paths or not rectified_paths:
        logger.error("One or both path files are empty. Cannot validate SC-005.")
        status = {
            "status": "fail",
            "reason": "Missing path data",
            "threshold": threshold,
            "measured_diff": None
        }
    else:
        # Create a map for quick lookup if IDs match, or assume order matches if generated sequentially
        # Ideally, we match by path_id or seed_id. Assuming the lists are aligned by generation order for this specific task scope.
        # If IDs exist, use them.
        diffs = []
        for i, rect_path in enumerate(rectified_paths):
            if i < len(raw_paths):
                raw_score = raw_paths[i].get('score', 0.0)
                rect_score = rect_path.get('score', 0.0)
                diffs.append(abs(rect_score - raw_score))
        
        if not diffs:
            logger.error("No overlapping paths found to compare scores.")
            status = {
                "status": "fail",
                "reason": "No overlapping paths",
                "threshold": threshold,
                "measured_diff": None
            }
        else:
            mean_diff = sum(diffs) / len(diffs)
            passed = mean_diff >= threshold
            
            logger.info(f"Mean Absolute Difference: {mean_diff:.6f} (Threshold: {threshold})")
            status = {
                "status": "pass" if passed else "fail",
                "threshold": threshold,
                "measured_diff": mean_diff,
                "num_paths_compared": len(diffs)
            }
    
    # Write output
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(status, f, indent=2)
    
    logger.info(f"SC-005 validation result written to {output_file}")
    return status

def main():
    parser = argparse.ArgumentParser(description="llmXive ProRL Evaluation Pipeline")
    parser.add_argument('--dataset', type=str, default='ml-latest-small', help='Dataset to use')
    parser.add_argument('--seed', type=str, default=None, help='Specific seed item ID (optional)')
    parser.add_argument('--k', type=int, default=10, help='K for evaluation metrics')
    parser.add_argument('--validate-sc005', action='store_true', help='Run SC-005 validation only')
    parser.add_argument('--raw-paths', type=str, default='code/results/greedy_paths.json', help='Path to raw paths JSON')
    parser.add_argument('--rectified-paths', type=str, default='code/results/greedy_rectified_paths.json', help='Path to rectified paths JSON')
    
    args = parser.parse_args()
    
    if args.validate_sc005:
        validate_sc005(
            raw_paths_file=args.raw_paths,
            rectified_paths_file=args.rectified_paths
        )
    else:
        run_evaluation_pipeline(
            dataset_name=args.dataset,
            seed_item_id=args.seed,
            k=args.k
        )
        # Automatically run validation after pipeline
        validate_sc005()

if __name__ == "__main__":
    main()
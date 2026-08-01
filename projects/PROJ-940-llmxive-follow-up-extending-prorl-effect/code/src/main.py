import argparse
import json
import os
import logging
from typing import List, Dict, Any, Optional
import numpy as np

from src.config import get_config
from src.data_loader import load_dataset, split_data
from src.graph_builder import build_graph, get_connected_component
from src.path_generator import generate_greedy_paths, apply_prorl_rectification
from src.evaluator import Evaluator
from src.exceptions import DataFetchError, GraphDisconnectionError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_paths_from_json(filepath: str) -> List[Dict[str, Any]]:
    """Load paths from a JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Path file not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def save_paths_to_json(paths: List[Dict[str, Any]], filepath: str) -> None:
    """Save paths to a JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(paths, f, indent=2)

def run_evaluation_pipeline(dataset_name: str, seed_item_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Run the full evaluation pipeline:
    1. Load data
    2. Build graph
    3. Generate paths (Greedy + Beam)
    4. Apply ProRL rectification
    5. Evaluate metrics
    6. Save results
    """
    config = get_config()
    
    # 1. Load Data
    logger.info(f"Loading dataset: {dataset_name}")
    try:
        data = load_dataset(dataset_name, streaming=True)
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise DataFetchError(f"Could not fetch dataset {dataset_name}: {e}")

    # 2. Build Graph
    logger.info("Building item similarity graph...")
    graph = build_graph(data, config)

    # 3. Generate Paths
    if seed_item_id:
        logger.info(f"Generating paths for seed item: {seed_item_id}")
        greedy_paths = generate_greedy_paths(graph, seed_item_id, config)
        beam_paths = [] # Placeholder for beam search if needed later
        
        # 4. Apply Rectification
        logger.info("Applying ProRL rectification...")
        rectified_paths = apply_prorl_rectification(greedy_paths, config)
        
        # 5. Save Intermediate Results
        save_paths_to_json(greedy_paths, 'results/greedy_paths.json')
        save_paths_to_json(rectified_paths, 'results/greedy_rectified_paths.json')
        
        return {
            "greedy_paths_count": len(greedy_paths),
            "rectified_paths_count": len(rectified_paths)
        }
    else:
        # Batch evaluation mode (US2)
        logger.info("Running batch evaluation on test set...")
        test_sessions = split_data(data, config)
        evaluator = Evaluator(test_sessions, graph, config)
        metrics = evaluator.run_evaluation()
        return metrics

def validate_sc005() -> Dict[str, Any]:
    """
    Validate SC-005: Verify mean absolute difference between rectified and raw scores >= 0.01.
    Reads from results/greedy_paths.json and results/greedy_rectified_paths.json.
    Writes status to results/sc005_status.json.
    """
    greedy_path_file = 'results/greedy_paths.json'
    rectified_path_file = 'results/greedy_rectified_paths.json'
    status_file = 'results/sc005_status.json'

    if not os.path.exists(greedy_path_file) or not os.path.exists(rectified_path_file):
        error_msg = f"Required files missing: {greedy_path_file} or {rectified_path_file}. Run pipeline first."
        logger.error(error_msg)
        status = {
            "status": "fail",
            "reason": error_msg,
            "mean_absolute_difference": None,
            "threshold": 0.01
        }
        os.makedirs('results', exist_ok=True)
        with open(status_file, 'w') as f:
            json.dump(status, f, indent=2)
        return status

    try:
        with open(greedy_path_file, 'r') as f:
            greedy_paths = json.load(f)
        with open(rectified_path_file, 'r') as f:
            rectified_paths = json.load(f)

        if len(greedy_paths) != len(rectified_paths):
            raise ValueError("Mismatch in number of paths between greedy and rectified files.")

        diffs = []
        for g_path, r_path in zip(greedy_paths, rectified_paths):
            if 'score' in g_path and 'score' in r_path:
                diff = abs(g_path['score'] - r_path['score'])
                diffs.append(diff)

        if not diffs:
            raise ValueError("No scores found in path data to compare.")

        mean_abs_diff = float(np.mean(diffs))
        threshold = 0.01
        passed = mean_abs_diff >= threshold

        status = {
            "status": "pass" if passed else "fail",
            "mean_absolute_difference": mean_abs_diff,
            "threshold": threshold,
            "sample_count": len(diffs)
        }

        os.makedirs('results', exist_ok=True)
        with open(status_file, 'w') as f:
            json.dump(status, f, indent=2)

        logger.info(f"SC-005 Validation: {'PASSED' if passed else 'FAILED'} (MAD={mean_abs_diff:.6f})")
        return status

    except Exception as e:
        logger.error(f"Error during SC-005 validation: {e}")
        status = {
            "status": "fail",
            "reason": str(e),
            "mean_absolute_difference": None,
            "threshold": 0.01
        }
        with open(status_file, 'w') as f:
            json.dump(status, f, indent=2)
        return status

def main():
    parser = argparse.ArgumentParser(description="llmXive ProRL Pipeline")
    parser.add_argument('--dataset', type=str, default='ml-latest-small', help='Dataset name')
    parser.add_argument('--seed', type=str, default=None, help='Seed item ID for single path generation')
    parser.add_argument('--validate-sc005', action='store_true', help='Run SC-005 validation only')
    
    args = parser.parse_args()

    if args.validate_sc005:
        validate_sc005()
    else:
        run_evaluation_pipeline(args.dataset, args.seed)

if __name__ == '__main__':
    main()
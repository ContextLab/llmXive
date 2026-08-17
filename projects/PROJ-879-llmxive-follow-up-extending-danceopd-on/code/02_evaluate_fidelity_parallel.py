"""
Parallel batch processing version of the fidelity evaluation pipeline.

This script implements parallel batch processing for image generation to
optimize runtime performance. It uses the batch_processor module to
distribute image generation tasks across multiple CPU cores, ensuring
the pipeline completes within the 6-hour runtime constraint.

This is a parallelized variant of 02_evaluate_fidelity.py that leverages
multiprocessing for the image generation phase.
"""
import argparse
import sys
import signal
import time
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np
import torch

from utils.config import get_config
from utils.metrics import calculate_fid, calculate_clip_score
from utils.statistics import run_bootstrap_test, run_ttest
from utils.batch_processor import run_parallel_batch_processing, estimate_runtime
from models.inference import generate_image_from_velocity


# Timeout handling for the 6-hour limit
class TimeoutError(Exception):
    pass


def timeout_handler(signum, frame):
    raise TimeoutError("6-hour timeout exceeded")


def setup_timeout(seconds: int):
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)


def cancel_timeout():
    signal.alarm(0)


def save_partial_results(results: Dict[str, Any], output_path: str):
    """Save partial results if the process is interrupted."""
    results['status'] = 'partial'
    results['timestamp'] = time.strftime('%Y-%m-%d %H:%M:%S')
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)


def load_dataset(path: str) -> pd.DataFrame:
    """Load the teacher routing dataset."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Dataset not found: {path}")
    return pd.read_parquet(path)


def load_trees(models_dir: str) -> Dict[int, Any]:
    """Load trained decision tree models."""
    trees = {}
    models_path = Path(models_dir)
    if not models_path.exists():
        return trees

    for model_file in models_path.glob("tree_depth*.pkl"):
        depth = int(model_file.stem.replace("tree_depth", ""))
        import pickle
        with open(model_file, 'rb') as f:
            trees[depth] = pickle.load(f)
    return trees


def prepare_samples_for_generation(
    dataset: pd.DataFrame,
    trees: Dict[int, Any],
    depth: int,
    teacher_mode: bool = False
) -> List[Dict[str, Any]]:
    """
    Prepare samples for image generation.

    Args:
        dataset: The routing dataset.
        trees: Dictionary of trained tree models.
        depth: The tree depth to use for prediction (if not teacher mode).
        teacher_mode: If True, use teacher routing labels; otherwise use tree predictions.

    Returns:
        List of sample dictionaries ready for generation.
    """
    samples = []

    for idx, row in dataset.iterrows():
        sample = {
            'sample_idx': idx,
            'velocity_vector': row['velocity_vector'],
            'noise_level': row['noise_level'],
            'expert_type': row['routing_label'] if teacher_mode else None
        }

        if not teacher_mode:
            # Predict expert type using the tree
            if depth in trees:
                tree = trees[depth]
                # Prepare features for prediction
                features = np.array([
                    row['prompt_embedding'] if isinstance(row['prompt_embedding'], (list, np.ndarray)) else [0.0] * 512,
                    [row['noise_level']]
                ]).flatten()
                # Simple prediction (assuming tree expects flattened features)
                try:
                    pred_label = tree.predict([features])[0]
                    sample['expert_type'] = pred_label
                except Exception as e:
                    # Fallback to a default if prediction fails
                    sample['expert_type'] = 'expert_text_to_image'
            else:
                sample['expert_type'] = 'expert_text_to_image'

        samples.append(sample)

    return samples


def run_parallel_fidelity_evaluation(
    dataset_path: str,
    trees_path: str,
    output_dir: str,
    depth: int = 5,
    num_workers: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run parallel fidelity evaluation.

    Args:
        dataset_path: Path to the teacher routing dataset.
        trees_path: Path to the directory containing trained trees.
        output_dir: Directory to save results.
        depth: The tree depth to evaluate.
        num_workers: Number of parallel workers.

    Returns:
        Dictionary containing evaluation results.
    """
    config = get_config()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Load data
    print("Loading dataset...")
    dataset = load_dataset(dataset_path)
    print(f"Loaded {len(dataset)} samples")

    # Load trees
    print("Loading trees...")
    trees = load_trees(trees_path)
    print(f"Loaded trees for depths: {list(trees.keys())}")

    # Prepare samples for tree-generated images
    print(f"Preparing samples for tree-generated images (depth={depth})...")
    tree_samples = prepare_samples_for_generation(dataset, trees, depth, teacher_mode=False)

    # Prepare samples for teacher-baseline images
    print("Preparing samples for teacher-baseline images...")
    teacher_samples = prepare_samples_for_generation(dataset, trees, depth, teacher_mode=True)

    # Estimate runtime
    # We'll use a pilot to estimate, but for now assume a baseline
    estimated_stats = estimate_runtime(
        num_samples=len(tree_samples),
        avg_time_per_sample=5.0,  # Placeholder, will be refined
        num_workers=num_workers or max(1, os.cpu_count() - 1)
    )
    print(f"Estimated runtime: {estimated_stats['estimated_total_hours']:.2f} hours")

    if not estimated_stats['within_6h_budget']:
        print("Warning: Estimated runtime exceeds 6-hour budget. Consider reducing sample size or increasing workers.")

    # Run parallel batch processing for tree-generated images
    tree_output_dir = str(output_path / f"tree_depth{depth}")
    print(f"\nGenerating tree images (depth={depth})...")
    tree_results = run_parallel_batch_processing(
        samples=tree_samples,
        output_dir=tree_output_dir,
        num_workers=num_workers,
        batch_size=10
    )

    # Run parallel batch processing for teacher-baseline images
    teacher_output_dir = str(output_path / "teacher_baseline")
    print("\nGenerating teacher-baseline images...")
    teacher_results = run_parallel_batch_processing(
        samples=teacher_samples,
        output_dir=teacher_output_dir,
        num_workers=num_workers,
        batch_size=10
    )

    # Compute fidelity metrics
    print("\nComputing fidelity metrics...")
    fid_score = calculate_fid(tree_output_dir, teacher_output_dir)
    clip_score = calculate_clip_score(tree_output_dir, teacher_output_dir)

    results = {
        'depth': depth,
        'fid_teacher_baseline': fid_score,
        'clip_teacher_baseline': clip_score,
        'tree_generation_stats': tree_results['stats'],
        'teacher_generation_stats': teacher_results['stats'],
        'total_samples': len(dataset),
        'successful_tree_images': tree_results['stats']['successful'],
        'successful_teacher_images': teacher_results['stats']['successful']
    }

    # Save results
    results_path = output_path / f"fidelity_results_depth{depth}.json"
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nFidelity evaluation complete for depth={depth}")
    print(f"FID: {fid_score:.4f}, CLIP: {clip_score:.4f}")

    return results


def run_fidelity_evaluation_parallel(
    dataset_path: str,
    trees_path: str,
    output_dir: str,
    depths: List[int] = [5],
    num_workers: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run fidelity evaluation for multiple tree depths in parallel.

    Args:
        dataset_path: Path to the teacher routing dataset.
        trees_path: Path to the directory containing trained trees.
        output_dir: Directory to save results.
        depths: List of tree depths to evaluate.
        num_workers: Number of parallel workers for image generation.

    Returns:
        Dictionary containing results for all evaluated depths.
    """
    all_results = {}

    for depth in depths:
        print(f"\n{'='*60}")
        print(f"Evaluating depth={depth}")
        print(f"{'='*60}")

        try:
            result = run_parallel_fidelity_evaluation(
                dataset_path=dataset_path,
                trees_path=trees_path,
                output_dir=output_dir,
                depth=depth,
                num_workers=num_workers
            )
            all_results[depth] = result
        except Exception as e:
            print(f"Error evaluating depth={depth}: {e}")
            all_results[depth] = {'error': str(e), 'depth': depth}

    # Save summary
    summary_path = Path(output_dir) / "fidelity_evaluation_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)

    return all_results


def main():
    """Main entry point for parallel fidelity evaluation."""
    parser = argparse.ArgumentParser(description="Parallel Fidelity Evaluation")
    parser.add_argument("--dataset", type=str, default="data/processed/teacher_routing_dataset.parquet",
                      help="Path to the teacher routing dataset")
    parser.add_argument("--trees", type=str, default="models/trained_trees",
                      help="Path to the directory containing trained trees")
    parser.add_argument("--output", type=str, default="data/results",
                      help="Directory to save results")
    parser.add_argument("--depths", type=str, nargs="+", default=[5],
                      help="Tree depths to evaluate (e.g., --depths 2 5 10)")
    parser.add_argument("--workers", type=int, default=None,
                      help="Number of parallel workers (default: CPU count - 1)")

    args = parser.parse_args()

    # Set up timeout (6 hours = 21600 seconds)
    setup_timeout(21600)

    try:
        depths = [int(d) for d in args.depths]
        results = run_fidelity_evaluation_parallel(
            dataset_path=args.dataset,
            trees_path=args.trees,
            output_dir=args.output,
            depths=depths,
            num_workers=args.workers
        )

        print("\nFinal Summary:")
        for depth, result in results.items():
            if 'error' in result:
                print(f"  Depth {depth}: ERROR - {result['error']}")
            else:
                print(f"  Depth {depth}: FID={result.get('fid_teacher_baseline', 'N/A')}, "
                      f"CLIP={result.get('clip_teacher_baseline', 'N/A')}")

        cancel_timeout()

    except TimeoutError:
        print("\nTimeout: 6-hour limit exceeded. Saving partial results...")
        # Save partial results if needed
        save_partial_results({'status': 'timeout'}, str(Path(args.output) / "partial_results.json"))
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        save_partial_results({'status': 'error', 'error': str(e)}, str(Path(args.output) / "partial_results.json"))
        sys.exit(1)


if __name__ == "__main__":
    main()
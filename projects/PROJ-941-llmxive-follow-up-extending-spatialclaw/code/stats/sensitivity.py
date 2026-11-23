"""
Sensitivity analysis module for SpatialClaw benchmark.

Implements sensitivity sweeps for depth-estimation thresholds and
edge-case analysis for "flat object" scenarios (zero depth variance).
"""
import json
import os
import csv
import logging
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from data.loader import load_dataset, DataLoadError

# Configure logger
logger = logging.getLogger(__name__)

def is_flat_object(
    task_data: Dict[str, Any], 
    epsilon: float = 0.0
) -> bool:
    """
    Determine if a task instance involves a "flat object" (zero depth variance).
    
    Args:
        task_data: The task instance dictionary containing ground_truth_3d_params.
        epsilon: Tolerance for considering depth variance as zero.
    
    Returns:
        True if the depth variance is <= epsilon, False otherwise.
    """
    try:
        gt_params = task_data.get("ground_truth_3d_params", {})
        # Depth variance is stored in the 3D parameters
        depth_variance = gt_params.get("depth_variance", 0.0)
        return depth_variance <= epsilon
    except (TypeError, KeyError) as e:
        logger.warning(f"Could not determine flatness for task {task_data.get('task_id')}: {e}")
        return False

def load_comparison_results_for_flat_analysis(
    paired_csv_path: str
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Load the final paired dataset and split into 2D and 3D results for analysis.
    
    Args:
        paired_csv_path: Path to the final_paired_dataset.csv.
    
    Returns:
        Tuple of (list of 2D results, list of 3D results) keyed by task_id.
    """
    if not os.path.exists(paired_csv_path):
        raise FileNotFoundError(f"Paired dataset not found at {paired_csv_path}")
    
    results_2d = {}
    results_3d = {}
    
    with open(paired_csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            task_id = row['task_id']
            # We assume the CSV contains aggregated 2D stats and single 3D stats
            # Schema: task_id, task_type, 2d_success_rate, 2d_mean_latency, 3d_success, 3d_latency
            results_2d[task_id] = {
                'task_type': row['task_type'],
                'success_rate': float(row['2d_success_rate']),
                'latency': float(row['2d_mean_latency'])
            }
            results_3d[task_id] = {
                'task_type': row['task_type'],
                'success': row['3d_success'].lower() == 'true' if isinstance(row['3d_success'], str) else bool(row['3d_success']),
                'latency': float(row['3d_latency'])
            }
    
    return list(results_2d.values()), list(results_3d.values())

def run_flat_object_sensitivity_analysis(
    dataset_path: str,
    paired_csv_path: str,
    output_path: str,
    epsilon_values: Optional[List[float]] = None
) -> Dict[str, Any]:
    """
    Perform sensitivity analysis on the "flat object" edge case.
    
    Varies the tolerance (epsilon) for "zero depth variance" and calculates
    the impact on success rates and latency differences for tasks classified
    as flat.
    
    Args:
        dataset_path: Path to the raw dataset JSON (synthetic_spatialclaw_v1.json).
        paired_csv_path: Path to the final_paired_dataset.csv.
        output_path: Path to write the results CSV.
        epsilon_values: List of epsilon thresholds to test. Defaults to [0.0, 0.01, 0.02, 0.05, 0.1].
    
    Returns:
        Dictionary containing the analysis summary.
    """
    if epsilon_values is None:
        epsilon_values = [0.0, 0.01, 0.02, 0.05, 0.1]
    
    logger.info(f"Loading dataset from {dataset_path}")
    try:
        dataset = load_dataset(dataset_path)
    except DataLoadError as e:
        logger.error(f"Failed to load dataset: {e}")
        raise
    
    logger.info(f"Loading paired results from {paired_csv_path}")
    # We need to map task_id to the ground truth depth variance from the dataset
    # and to the performance metrics from the paired CSV.
    task_gt_map = {}
    for item in dataset:
        task_id = item.get('task_id')
        if not task_id:
            continue
        gt_params = item.get('ground_truth_3d_params', {})
        depth_variance = gt_params.get('depth_variance', 0.0)
        task_gt_map[task_id] = {
            'depth_variance': depth_variance,
            'task_type': item.get('task_type')
        }
    
    # Load performance results
    # We need to re-associate performance with task_id.
    # The paired CSV has task_id, so we can join on that.
    perf_map = {}
    if os.path.exists(paired_csv_path):
        with open(paired_csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                perf_map[row['task_id']] = row
    else:
        logger.warning(f"Paired CSV not found at {paired_csv_path}. Skipping performance analysis.")
    
    results = []
    
    for epsilon in epsilon_values:
        logger.info(f"Processing epsilon={epsilon}")
        flat_tasks = []
        non_flat_tasks = []
        
        for task_id, gt_info in task_gt_map.items():
            if gt_info['depth_variance'] <= epsilon:
                flat_tasks.append(task_id)
            else:
                non_flat_tasks.append(task_id)
        
        # Calculate metrics for flat tasks
        flat_success_rates = []
        flat_latency_diffs = []
        flat_count = 0
        
        for tid in flat_tasks:
            if tid in perf_map:
                row = perf_map[tid]
                try:
                    # 2D success rate
                    sr = float(row['2d_success_rate'])
                    flat_success_rates.append(sr)
                    
                    # Latency diff (2D - 3D)
                    lat_2d = float(row['2d_mean_latency'])
                    lat_3d = float(row['3d_latency'])
                    diff = lat_2d - lat_3d
                    flat_latency_diffs.append(diff)
                    flat_count += 1
                except (ValueError, KeyError) as e:
                    logger.debug(f"Could not parse metrics for {tid}: {e}")
        
        # Calculate metrics for non-flat tasks (baseline for comparison)
        non_flat_success_rates = []
        non_flat_latency_diffs = []
        non_flat_count = 0
        
        for tid in non_flat_tasks:
            if tid in perf_map:
                row = perf_map[tid]
                try:
                    sr = float(row['2d_success_rate'])
                    non_flat_success_rates.append(sr)
                    
                    lat_2d = float(row['2d_mean_latency'])
                    lat_3d = float(row['3d_latency'])
                    diff = lat_2d - lat_3d
                    non_flat_latency_diffs.append(diff)
                    non_flat_count += 1
                except (ValueError, KeyError) as e:
                    logger.debug(f"Could not parse metrics for {tid}: {e}")
        
        # Compute aggregates
        avg_flat_sr = np.mean(flat_success_rates) if flat_success_rates else 0.0
        avg_flat_lat_diff = np.mean(flat_latency_diffs) if flat_latency_diffs else 0.0
        avg_non_flat_sr = np.mean(non_flat_success_rates) if non_flat_success_rates else 0.0
        avg_non_flat_lat_diff = np.mean(non_flat_latency_diffs) if non_flat_latency_diffs else 0.0
        
        results.append({
            'epsilon': epsilon,
            'flat_task_count': flat_count,
            'non_flat_task_count': non_flat_count,
            'flat_mean_success_rate': avg_flat_sr,
            'flat_mean_latency_diff_ms': avg_flat_lat_diff,
            'non_flat_mean_success_rate': avg_non_flat_sr,
            'non_flat_mean_latency_diff_ms': avg_non_flat_lat_diff
        })
    
    # Write results to CSV
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fieldnames = [
        'epsilon', 'flat_task_count', 'non_flat_task_count',
        'flat_mean_success_rate', 'flat_mean_latency_diff_ms',
        'non_flat_mean_success_rate', 'non_flat_mean_latency_diff_ms'
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Flat object sensitivity analysis complete. Results written to {output_path}")
    
    return {
        'output_path': output_path,
        'epsilon_values': epsilon_values,
        'total_tasks_analyzed': len(task_gt_map),
        'results': results
    }

def write_flat_object_sensitivity_csv(
    results: List[Dict[str, Any]],
    output_path: str
) -> None:
    """
    Helper to write sensitivity results to CSV.
    
    Args:
        results: List of result dictionaries from the analysis.
        output_path: Path to write the CSV.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fieldnames = list(results[0].keys())
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

def main():
    """
    Main entry point for running the flat object sensitivity analysis.
    
    Usage:
        python -m code.stats.sensitivity \
            --dataset data/raw/synthetic_spatialclaw_v1.json \
            --paired results/analysis/final_paired_dataset.csv \
            --output results/analysis/flat_object_sensitivity.csv
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Run flat object sensitivity analysis")
    parser.add_argument(
        "--dataset", 
        type=str, 
        default="data/raw/synthetic_spatialclaw_v1.json",
        help="Path to the raw dataset JSON"
    )
    parser.add_argument(
        "--paired", 
        type=str, 
        default="results/analysis/final_paired_dataset.csv",
        help="Path to the final paired dataset CSV"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="results/analysis/flat_object_sensitivity.csv",
        help="Path to write the output CSV"
    )
    parser.add_argument(
        "--epsilons",
        type=float,
        nargs="+",
        default=[0.0, 0.01, 0.02, 0.05, 0.1],
        help="Space-separated list of epsilon values to test"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        run_flat_object_sensitivity_analysis(
            dataset_path=args.dataset,
            paired_csv_path=args.paired,
            output_path=args.output,
            epsilon_values=args.epsilons
        )
        logger.info("Analysis completed successfully.")
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
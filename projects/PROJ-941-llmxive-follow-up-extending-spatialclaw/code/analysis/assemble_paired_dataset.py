"""
Assemble the final paired dataset by merging 2D agent results and 3D baseline results.

This module aggregates the 2D agent runs (across multiple seeds/runs per task)
and pairs them with the single 3D baseline run per task to create a canonical
comparison dataset for statistical analysis.

Output: results/analysis/final_paired_dataset.csv
"""
import os
import json
import csv
import logging
import argparse
from typing import Dict, List, Any, Optional, Set
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_yaml_config_simple(config_path: str) -> Dict[str, Any]:
    """
    Load a simple YAML config file (key: value pairs).
    Handles basic types and comments.
    """
    config = {}
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                # Try to parse as int, float, bool, or keep as string
                if value.lower() == 'true':
                    config[key] = True
                elif value.lower() == 'false':
                    config[key] = False
                else:
                    try:
                        if '.' in value:
                            config[key] = float(value)
                        else:
                            config[key] = int(value)
                    except ValueError:
                        config[key] = value
    return config

def load_baseline_results(baseline_path: str) -> Dict[str, Dict[str, Any]]:
    """
    Load the 3D baseline results from a JSON file.
    Returns a dict keyed by task_id.
    """
    if not os.path.exists(baseline_path):
        raise FileNotFoundError(f"Baseline results file not found: {baseline_path}")
    
    with open(baseline_path, 'r') as f:
        data = json.load(f)
    
    # Handle both list and dict formats
    if isinstance(data, list):
        baseline_map = {}
        for item in data:
            if 'task_id' not in item:
                logger.warning(f"Skipping item without task_id in baseline results")
                continue
            baseline_map[item['task_id']] = item
    elif isinstance(data, dict):
        baseline_map = data
    else:
        raise ValueError(f"Unexpected baseline results format: {type(data)}")
    
    logger.info(f"Loaded {len(baseline_map)} baseline results")
    return baseline_map

def load_2d_run_results(run_dir: str) -> List[Dict[str, Any]]:
    """
    Load all 2D agent run results from the results/runs directory.
    Returns a list of all result dicts from all run_*.json files.
    """
    if not os.path.exists(run_dir):
        raise FileNotFoundError(f"2D run results directory not found: {run_dir}")
    
    all_results = []
    run_files = sorted(glob.glob(os.path.join(run_dir, "run_*.json")))
    
    if not run_files:
        raise FileNotFoundError(f"No run_*.json files found in {run_dir}")
    
    for run_file in run_files:
        with open(run_file, 'r') as f:
            run_data = json.load(f)
        
        # Handle both list and dict formats
        if isinstance(run_data, list):
            all_results.extend(run_data)
        elif isinstance(run_data, dict):
            if 'results' in run_data and isinstance(run_data['results'], list):
                all_results.extend(run_data['results'])
            else:
                # Single result object
                all_results.append(run_data)
        else:
            logger.warning(f"Skipping unexpected format in {run_file}")
    
    logger.info(f"Loaded {len(all_results)} total 2D agent results from {len(run_files)} files")
    return all_results

def aggregate_2d_results(
    run_results: List[Dict[str, Any]], 
    n_runs_expected: int
) -> Dict[str, Dict[str, Any]]:
    """
    Aggregate 2D agent results by task_id.
    Calculates success_rate and mean_latency for each task.
    """
    aggregated = {}
    
    for result in run_results:
        task_id = result.get('task_id')
        if not task_id:
            logger.warning(f"Skipping result without task_id")
            continue
        
        if task_id not in aggregated:
            aggregated[task_id] = {
                'successes': 0,
                'latencies': [],
                'task_type': result.get('task_type', 'unknown')
            }
        
        if result.get('success', False):
            aggregated[task_id]['successes'] += 1
        
        latency = result.get('latency_ms')
        if latency is not None:
            aggregated[task_id]['latencies'].append(latency)
    
    # Calculate final metrics
    final_aggregated = {}
    for task_id, data in aggregated.items():
        total_runs = len(data['latencies'])
        if total_runs == 0:
            logger.warning(f"No latency data for task {task_id}, skipping")
            continue
        
        success_rate = data['successes'] / total_runs
        mean_latency = sum(data['latencies']) / total_runs
        
        final_aggregated[task_id] = {
            '2d_success_rate': success_rate,
            '2d_mean_latency': mean_latency,
            'task_type': data['task_type'],
            'n_runs': total_runs
        }
    
    logger.info(f"Aggregated {len(final_aggregated)} unique tasks from 2D results")
    return final_aggregated

def build_paired_dataset(
    baseline_map: Dict[str, Dict[str, Any]],
    aggregated_2d: Dict[str, Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Build the paired dataset by merging baseline and aggregated 2D results.
    Only includes tasks that have both 2D and 3D results.
    """
    paired = []
    common_tasks = set(baseline_map.keys()) & set(aggregated_2d.keys())
    
    if not common_tasks:
        logger.error("No common tasks found between baseline and 2D results!")
        return paired
    
    logger.info(f"Found {len(common_tasks)} common tasks for pairing")
    
    for task_id in common_tasks:
        baseline = baseline_map[task_id]
        agg_2d = aggregated_2d[task_id]
        
        task_type = agg_2d['task_type']
        
        # Extract baseline metrics
        baseline_success = baseline.get('success', False)
        baseline_latency = baseline.get('latency_ms')
        
        # Extract 2D metrics
        d_success_rate = agg_2d['2d_success_rate']
        d_mean_latency = agg_2d['2d_mean_latency']
        
        # Calculate differences
        success_diff = d_success_rate - (1.0 if baseline_success else 0.0)
        latency_diff = d_mean_latency - baseline_latency if baseline_latency is not None else None
        
        row = {
            'task_id': task_id,
            'task_type': task_type,
            '2d_success_rate': d_success_rate,
            '2d_mean_latency': d_mean_latency,
            '3d_success': 1 if baseline_success else 0,
            '3d_latency': baseline_latency if baseline_latency is not None else 0.0,
            'success_diff': success_diff,
            'latency_diff': latency_diff
        }
        
        paired.append(row)
    
    # Sort by task_id
    paired.sort(key=lambda x: x['task_id'])
    
    logger.info(f"Built paired dataset with {len(paired)} rows")
    return paired

def write_csv(data: List[Dict[str, Any]], output_path: str) -> None:
    """
    Write the paired dataset to a CSV file.
    Validates for null values in critical columns before writing.
    """
    if not data:
        raise ValueError("No data to write")
    
    # Define critical columns that must not be null
    critical_columns = ['task_id', 'task_type', '2d_success_rate', '2d_mean_latency', 
                      '3d_success', '3d_latency', 'success_diff', 'latency_diff']
    
    # Validate data
    for i, row in enumerate(data):
        for col in critical_columns:
            if col not in row or row[col] is None:
                raise ValueError(f"Row {i} missing or null value in critical column: {col}")
    
    # Write to CSV
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    fieldnames = ['task_id', 'task_type', '2d_success_rate', '2d_mean_latency', 
                 '3d_success', '3d_latency', 'success_diff', 'latency_diff']
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    logger.info(f"Wrote {len(data)} rows to {output_path}")

def main():
    """Main entry point for assembling the paired dataset."""
    parser = argparse.ArgumentParser(description="Assemble final paired dataset")
    parser.add_argument(
        '--config', 
        type=str, 
        default='data/power_config.yaml',
        help='Path to power config file'
    )
    parser.add_argument(
        '--baseline',
        type=str,
        default='results/logs/baseline_run.json',
        help='Path to 3D baseline results'
    )
    parser.add_argument(
        '--runs-dir',
        type=str,
        default='results/runs',
        help='Directory containing 2D agent run results'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='results/analysis/final_paired_dataset.csv',
        help='Output path for the paired dataset CSV'
    )
    args = parser.parse_args()
    
    try:
        # Load config to get n_runs expected (optional validation)
        config = load_yaml_config_simple(args.config)
        n_runs_expected = config.get('n_runs', 5)
        
        logger.info(f"Loading baseline results from {args.baseline}")
        baseline_map = load_baseline_results(args.baseline)
        
        logger.info(f"Loading 2D run results from {args.runs_dir}")
        run_results = load_2d_run_results(args.runs_dir)
        
        logger.info(f"Aggregating 2D results (expected {n_runs_expected} runs per task)")
        aggregated_2d = aggregate_2d_results(run_results, n_runs_expected)
        
        logger.info("Building paired dataset")
        paired_data = build_paired_dataset(baseline_map, aggregated_2d)
        
        logger.info(f"Writing output to {args.output}")
        write_csv(paired_data, args.output)
        
        logger.info("Paired dataset assembly completed successfully")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()

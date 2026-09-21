"""
Result Aggregator for BES (Bidirectional Evolutionary Search) experiments.

This module aggregates logs from individual BES loop executions (T024b-exec)
across different complexity parameters (N) into a single consolidated result file.
"""

import json
import os
import sys
import logging
import glob
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict, field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class AggregatedRunStats:
    """Statistics for a single parameter set (N) run."""
    n_value: int
    total_instances: int
    successful_instances: int
    failed_instances: int
    success_rate: float
    total_time_seconds: float
    avg_time_per_instance: float
    total_energy_joules: float
    avg_energy_per_instance: float
    population_size: int
    generations: int
    method: str  # 'symbolic' or 'neural'
    run_id: str
    timestamp: str

@dataclass
class AggregatedResult:
    """Container for all aggregated results."""
    experiment_id: str
    method: str
    runs: List[Dict[str, Any]] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


def load_json_file(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Load a JSON file and return its contents.

    Args:
        file_path: Path to the JSON file

    Returns:
        Dictionary containing the JSON data, or None if loading fails
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        return None


def find_run_logs(pattern: str) -> List[str]:
    """
    Find all log files matching the given glob pattern.

    Args:
        pattern: Glob pattern (e.g., 'data/processed/bes_n*_symbolic.json')

    Returns:
        List of file paths matching the pattern
    """
    files = glob.glob(pattern)
    if not files:
        logger.warning(f"No files found matching pattern: {pattern}")
    else:
        logger.info(f"Found {len(files)} log files matching pattern: {pattern}")
    return sorted(files)


def parse_n_from_filename(filename: str) -> Optional[int]:
    """
    Extract the N value from a filename.

    Expected formats:
    - bes_N{N}_{method}.json
    - bes_n{N}_{method}.json
    - bes_results_N{N}.json

    Args:
        filename: The filename to parse

    Returns:
        The N value as an integer, or None if parsing fails
    """
    import re
    # Try common patterns
    patterns = [
        r'.*bes[_-]N(\d+)[_-].*\.json',
        r'.*bes[_-]n(\d+)[_-].*\.json',
        r'.*bes_results[_-]N(\d+).*\.json',
        r'.*bes_results[_-]n(\d+).*\.json',
    ]

    for pattern in patterns:
        match = re.search(pattern, filename, re.IGNORECASE)
        if match:
            return int(match.group(1))

    logger.warning(f"Could not extract N value from filename: {filename}")
    return None


def aggregate_results(log_files: List[str]) -> AggregatedResult:
    """
    Aggregate results from multiple log files into a single structure.

    Args:
        log_files: List of paths to log files to aggregate

    Returns:
        AggregatedResult containing all combined data
    """
    if not log_files:
        raise ValueError("No log files provided for aggregation")

    runs = []
    method = None
    experiment_id = None

    for log_file in log_files:
        logger.info(f"Processing log file: {log_file}")
        data = load_json_file(log_file)

        if data is None:
            logger.warning(f"Skipping invalid log file: {log_file}")
            continue

        # Extract metadata from the log
        n_value = data.get('n_value') or data.get('N') or data.get('n')
        if n_value is None:
            # Try to extract from filename
            n_value = parse_n_from_filename(log_file)

        if n_value is None:
            logger.warning(f"Could not determine N value for {log_file}")
            continue

        # Determine method (symbolic or neural)
        file_method = data.get('method')
        if file_method:
            if method is None:
                method = file_method
            elif method != file_method:
                logger.warning(f"Method mismatch: expected {method}, got {file_method} in {log_file}")

        # Determine experiment_id
        exp_id = data.get('experiment_id')
        if exp_id:
            if experiment_id is None:
                experiment_id = exp_id
            elif experiment_id != exp_id:
                logger.warning(f"Experiment ID mismatch in {log_file}")

        # Calculate statistics
        instances = data.get('instances', [])
        total_instances = len(instances)
        successful = sum(1 for inst in instances if inst.get('success', False))
        failed = total_instances - successful
        success_rate = successful / total_instances if total_instances > 0 else 0.0

        total_time = sum(inst.get('elapsed_time', 0) for inst in instances)
        avg_time = total_time / total_instances if total_instances > 0 else 0.0

        total_energy = sum(inst.get('energy_joules', 0) for inst in instances)
        avg_energy = total_energy / total_instances if total_instances > 0 else 0.0

        # Create aggregated run stats
        run_stats = {
            'n_value': n_value,
            'total_instances': total_instances,
            'successful_instances': successful,
            'failed_instances': failed,
            'success_rate': success_rate,
            'total_time_seconds': total_time,
            'avg_time_per_instance': avg_time,
            'total_energy_joules': total_energy,
            'avg_energy_per_instance': avg_energy,
            'population_size': data.get('population_size', 0),
            'generations': data.get('generations', 0),
            'method': method or data.get('method', 'unknown'),
            'run_id': data.get('run_id', ''),
            'timestamp': data.get('timestamp', ''),
            'source_file': os.path.basename(log_file)
        }

        runs.append(run_stats)

        # Store full data for reference
        data['_aggregated_stats'] = run_stats
        data['_source_file'] = os.path.basename(log_file)

    if not runs:
        raise ValueError("No valid runs found in provided log files")

    # Determine method and experiment_id if not set
    if method is None:
        method = runs[0]['method']

    if experiment_id is None:
        experiment_id = f"agg_{method}_{len(runs)}_runs"

    # Create summary statistics
    avg_success_rate = sum(r['success_rate'] for r in runs) / len(runs)
    total_instances_all = sum(r['total_instances'] for r in runs)
    total_successful_all = sum(r['successful_instances'] for r in runs)
    overall_success_rate = total_successful_all / total_instances_all if total_instances_all > 0 else 0.0

    summary = {
        'total_runs': len(runs),
        'n_values': sorted([r['n_value'] for r in runs]),
        'overall_success_rate': overall_success_rate,
        'avg_success_rate': avg_success_rate,
        'total_instances': total_instances_all,
        'total_successful': total_successful_all,
        'method': method
    }

    metadata = {
        'aggregation_timestamp': datetime.now().isoformat(),
        'source_files': [os.path.basename(f) for f in log_files],
        'aggregation_version': '1.0.0'
    }

    return AggregatedResult(
        experiment_id=experiment_id,
        method=method,
        runs=runs,
        summary=summary,
        metadata=metadata
    )


def save_results(result: AggregatedResult, output_path: str) -> bool:
    """
    Save aggregated results to a JSON file.

    Args:
        result: The AggregatedResult to save
        output_path: Path to the output file

    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        # Convert to dictionary
        result_dict = {
            'experiment_id': result.experiment_id,
            'method': result.method,
            'runs': result.runs,
            'summary': result.summary,
            'metadata': result.metadata
        }

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result_dict, f, indent=2, default=str)

        logger.info(f"Successfully saved aggregated results to: {output_path}")
        return True

    except Exception as e:
        logger.error(f"Error saving results to {output_path}: {e}")
        return False


def main():
    """
    Main entry point for the result aggregator.

    Usage:
        python code/bes/result_aggregator.py --input-pattern "data/processed/bes_n*_symbolic.json" --output data/processed/bes_results.json

    This command aggregates all BES run logs matching the pattern into a single result file.
    """
    import argparse
    from datetime import datetime

    parser = argparse.ArgumentParser(
        description='Aggregate BES experiment results from multiple log files.'
    )
    parser.add_argument(
        '--input-pattern',
        type=str,
        required=True,
        help='Glob pattern to match input log files (e.g., "data/processed/bes_n*_symbolic.json")'
    )
    parser.add_argument(
        '--output',
        type=str,
        required=True,
        help='Output path for the aggregated results JSON file'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info(f"Starting result aggregation with pattern: {args.input_pattern}")

    # Find log files
    log_files = find_run_logs(args.input_pattern)

    if not log_files:
        logger.error("No log files found. Aborting.")
        sys.exit(1)

    # Aggregate results
    try:
        result = aggregate_results(log_files)
    except ValueError as e:
        logger.error(f"Aggregation failed: {e}")
        sys.exit(1)

    # Save results
    if not save_results(result, args.output):
        logger.error("Failed to save results.")
        sys.exit(1)

    logger.info(f"Aggregation complete. Summary: {result.summary}")
    sys.exit(0)


if __name__ == '__main__':
    main()

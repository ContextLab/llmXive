"""
Result Aggregator for BES (Bidirectional Evolutionary Search) experiments.

This module aggregates logs from multiple parameter sets (N values) generated
by T024b-exec into a single consolidated result file:
`data/processed/bes_results.json`.

It reads N-specific log files (typically named `bes_N{N}.json` or similar),
parses the `n` parameter from the filename or content, and merges the
statistics into a unified report.
"""

import json
import os
import sys
import logging
import glob
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class AggregatedRunStats:
    """Statistics for a single run (specific N)."""
    n: int
    success_rate: float
    total_runs: int
    successful_runs: int
    avg_time_per_run: float
    avg_memory_peak_mb: float
    total_energy_joules: float
    exclusions_count: int
    runtime_details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AggregatedResult:
    """The final aggregated result structure."""
    experiment_id: str
    total_parameters_tested: int
    parameter_sets: List[Dict[str, Any]]
    summary_statistics: Dict[str, Any]
    generated_at: str


def load_json_file(file_path: str) -> Optional[Dict[str, Any]]:
    """Safely load a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in {file_path}: {e}")
        return None


def find_run_logs(base_dir: str, pattern: str = "bes_N*.json") -> List[str]:
    """
    Find all log files matching the pattern in the base directory.
    Expected pattern: bes_N{N}.json
    """
    search_path = os.path.join(base_dir, pattern)
    logs = glob.glob(search_path)
    if not logs:
        # Try alternative pattern if standard one fails
        search_path_alt = os.path.join(base_dir, "run_*.json")
        logs = glob.glob(search_path_alt)
    return sorted(logs)


def parse_n_from_filename(filename: str) -> Optional[int]:
    """
    Extract the N value from a filename like 'bes_N100.json' or 'run_N50.json'.
    Returns None if N cannot be parsed.
    """
    basename = os.path.basename(filename)
    # Look for N followed by digits
    import re
    match = re.search(r'N(\d+)', basename)
    if match:
        return int(match.group(1))
    return None


def aggregate_results(log_files: List[str]) -> List[AggregatedRunStats]:
    """
    Aggregate results from a list of log files into AggregatedRunStats objects.
    """
    aggregated = []
    for log_file in log_files:
        data = load_json_file(log_file)
        if not data:
            continue

        # Try to extract N from filename first
        n = parse_n_from_filename(log_file)
        if n is None and 'n' in data:
            n = data.get('n')
        
        if n is None:
            logger.warning(f"Could not determine N for file: {log_file}")
            continue

        # Extract metrics based on expected log structure from T024b-exec
        # Expected structure: { "n": ..., "success_rate": ..., "total_runs": ..., ... }
        stats = AggregatedRunStats(
            n=n,
            success_rate=data.get('success_rate', 0.0),
            total_runs=data.get('total_runs', 0),
            successful_runs=data.get('successful_runs', 0),
            avg_time_per_run=data.get('avg_time_per_run', 0.0),
            avg_memory_peak_mb=data.get('avg_memory_peak_mb', 0.0),
            total_energy_joules=data.get('total_energy_joules', 0.0),
            exclusions_count=data.get('exclusions_count', 0),
            runtime_details=data.get('runtime_details', {})
        )
        aggregated.append(stats)

    # Sort by N
    aggregated.sort(key=lambda x: x.n)
    return aggregated


def save_results(results: List[AggregatedRunStats], output_path: str) -> bool:
    """
    Save the aggregated results to a single JSON file.
    """
    try:
        # Prepare the output structure
        from datetime import datetime
        output_data = {
            "experiment_id": "T024c_aggregated_bes_results",
            "total_parameters_tested": len(results),
            "parameter_sets": [asdict(r) for r in results],
            "summary_statistics": {
                "min_n": results[0].n if results else 0,
                "max_n": results[-1].n if results else 0,
                "avg_success_rate": sum(r.success_rate for r in results) / len(results) if results else 0.0,
                "total_experiments": sum(r.total_runs for r in results)
            },
            "generated_at": datetime.utcnow().isoformat()
        }

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"Successfully saved aggregated results to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save results: {e}")
        return False


def main():
    """
    Main entry point for the result aggregator.
    Reads logs from data/processed and writes to data/processed/bes_results.json.
    """
    # Default paths
    base_dir = "data/processed"
    output_file = os.path.join(base_dir, "bes_results.json")

    # Allow CLI override for base directory
    if len(sys.argv) > 1:
        base_dir = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]

    logger.info(f"Searching for logs in: {base_dir}")
    log_files = find_run_logs(base_dir)

    if not log_files:
        logger.warning("No log files found. Creating empty result file.")
        # Create a minimal valid output even if no logs found
        from datetime import datetime
        empty_result = {
            "experiment_id": "T024c_aggregated_bes_results",
            "total_parameters_tested": 0,
            "parameter_sets": [],
            "summary_statistics": {
                "min_n": 0,
                "max_n": 0,
                "avg_success_rate": 0.0,
                "total_experiments": 0
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(empty_result, f, indent=2)
        return 0

    logger.info(f"Found {len(log_files)} log files to aggregate.")
    results = aggregate_results(log_files)

    if not results:
        logger.warning("No valid results extracted from logs.")
        return 1

    success = save_results(results, output_file)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
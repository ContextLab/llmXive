"""
Threshold Sweep Aggregator

Aggregates results from the threshold identification raw analysis into a
single CSV file for downstream visualization and reporting.

Reads: data/processed/threshold_identification_raw.json
Writes: data/processed/threshold_sweep_results.csv
"""
import csv
import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure imports work relative to project root when run as module
try:
    from utils.config import get_project_paths
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from utils.config import get_project_paths

logger = logging.getLogger(__name__)

def load_threshold_identification_raw(path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Load the raw threshold identification JSON file.

    Args:
        path: Path to the JSON file. If None, uses project config.

    Returns:
        List of dictionaries containing threshold analysis results.
    """
    if path is None:
        paths = get_project_paths()
        path = paths["processed"] / "threshold_identification_raw.json"

    if not path.exists():
        raise FileNotFoundError(f"Raw threshold identification file not found: {path}")

    with open(path, 'r') as f:
        data = json.load(f)

    # Handle both list format and dict with 'results' key
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'results' in data:
        return data['results']
    else:
        raise ValueError(f"Unexpected JSON structure in {path}")

def aggregate_sweep_results_to_csv(
    input_path: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> Path:
    """
    Aggregate threshold identification results into a CSV file.

    The CSV contains columns for:
    - N: Matrix dimension
    - theta: Perturbation strength
    - outlier_probability: Fraction of runs with outliers
    - mean_max_eigenvalue: Mean of max eigenvalues across runs
    - std_max_eigenvalue: Standard deviation of max eigenvalues
    - num_runs: Number of Monte Carlo iterations

    Args:
        input_path: Path to threshold_identification_raw.json
        output_path: Path for output CSV

    Returns:
        Path to the created CSV file
    """
    if input_path is None:
        paths = get_project_paths()
        input_path = paths["processed"] / "threshold_identification_raw.json"

    if output_path is None:
        paths = get_project_paths()
        output_path = paths["processed"] / "threshold_sweep_results.csv"

    # Load raw data
    results = load_threshold_identification_raw(input_path)

    if not results:
        logger.warning("No results found in threshold identification raw file")
        # Create empty CSV with headers
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['N', 'theta', 'outlier_probability', 'mean_max_eigenvalue', 'std_max_eigenvalue', 'num_runs'])
        return output_path

    # Write CSV
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['N', 'theta', 'outlier_probability', 'mean_max_eigenvalue', 'std_max_eigenvalue', 'num_runs'])

        for entry in results:
            row = [
                entry.get('N', 0),
                entry.get('theta', 0.0),
                entry.get('outlier_probability', 0.0),
                entry.get('mean_max_eigenvalue', 0.0),
                entry.get('std_max_eigenvalue', 0.0),
                entry.get('num_runs', 0)
            ]
            writer.writerow(row)

    logger.info(f"Aggregated {len(results)} results to {output_path}")
    return output_path

def main():
    """Main entry point for the aggregator."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        output_path = aggregate_sweep_results_to_csv()
        logger.info(f"Successfully created {output_path}")
        return 0
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Error aggregating results: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())

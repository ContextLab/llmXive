"""
T021b: Analyze Monte Carlo results to prepare data for threshold identification.

This script reads the Monte Carlo results CSV, aggregates the data by perturbation
strength (theta), calculates the empirical probability of outlier emergence for
each theta value, and outputs a JSON file suitable for subsequent curve fitting.

Input: data/processed/mc_results.csv
Output: data/processed/threshold_identification_raw.json
"""
import os
import csv
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_mc_results(csv_path: Path) -> List[Dict[str, Any]]:
    """
    Load Monte Carlo results from CSV.

    Expected schema: run_id, N, theta, seed, outlier_count, max_eigenvalue
    """
    results = []
    if not csv_path.exists():
        raise FileNotFoundError(f"Monte Carlo results file not found: {csv_path}")

    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            parsed_row = {
                'run_id': row['run_id'],
                'N': int(row['N']),
                'theta': float(row['theta']),
                'seed': int(row['seed']),
                'outlier_count': int(row['outlier_count']),
                'max_eigenvalue': float(row['max_eigenvalue'])
            }
            results.append(parsed_row)

    if not results:
        raise ValueError(f"No data found in {csv_path}")

    logger.info(f"Loaded {len(results)} Monte Carlo iterations from {csv_path}")
    return results

def aggregate_by_theta(results: List[Dict[str, Any]]) -> Dict[float, Dict[str, Any]]:
    """
    Aggregate results by theta value.

    Calculates:
    - total_runs: number of iterations for this theta
    - outlier_count: total number of runs where an outlier was detected
    - outlier_probability: fraction of runs with outliers
    - max_eigenvalue_mean: mean of the maximum eigenvalues
    - max_eigenvalue_std: standard deviation of the maximum eigenvalues
    """
    theta_groups: Dict[float, List[Dict[str, Any]]] = {}

    # Group by theta
    for result in results:
        theta = result['theta']
        if theta not in theta_groups:
            theta_groups[theta] = []
        theta_groups[theta].append(result)

    # Aggregate statistics
    aggregated = {}
    for theta, group in sorted(theta_groups.items()):
        total_runs = len(group)
        outliers = sum(1 for r in group if r['outlier_count'] > 0)
        max_eigenvalues = [r['max_eigenvalue'] for r in group]

        aggregated[theta] = {
            'theta': theta,
            'total_runs': total_runs,
            'outlier_count': outliers,
            'outlier_probability': outliers / total_runs if total_runs > 0 else 0.0,
            'max_eigenvalue_mean': float(np.mean(max_eigenvalues)),
            'max_eigenvalue_std': float(np.std(max_eigenvalues)),
            'max_eigenvalue_min': float(np.min(max_eigenvalues)),
            'max_eigenvalue_max': float(np.max(max_eigenvalues))
        }

    logger.info(f"Aggregated data into {len(aggregated)} theta groups")
    return aggregated

def prepare_threshold_data(aggregated: Dict[float, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Prepare the final data structure for threshold identification.

    This includes metadata and the aggregated statistics sorted by theta.
    """
    sorted_thetas = sorted(aggregated.keys())

    data_points = [
        {
            'theta': theta,
            'outlier_probability': aggregated[theta]['outlier_probability'],
            'total_runs': aggregated[theta]['total_runs'],
            'outlier_count': aggregated[theta]['outlier_count'],
            'max_eigenvalue_mean': aggregated[theta]['max_eigenvalue_mean'],
            'max_eigenvalue_std': aggregated[theta]['max_eigenvalue_std']
        }
        for theta in sorted_thetas
    ]

    # Check for monotonicity (basic sanity check)
    probs = [d['outlier_probability'] for d in data_points]
    is_monotonic = all(probs[i] <= probs[i+1] + 1e-9 for i in range(len(probs)-1))

    return {
        'metadata': {
            'source_file': 'mc_results.csv',
            'description': 'Aggregated Monte Carlo results for threshold identification',
            'generated_at': str(Path.cwd()),
            'data_points_count': len(data_points),
            'monotonicity_check': is_monotonic,
            'theoretical_edge': 2.0,
            'bbp_threshold_note': 'Outlier expected when theta > 2.0'
        },
        'data': data_points
    }

def main():
    """Main entry point for T021b."""
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    input_csv = project_root / 'data' / 'processed' / 'mc_results.csv'
    output_json = project_root / 'data' / 'processed' / 'threshold_identification_raw.json'

    # Ensure output directory exists
    output_json.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Load raw Monte Carlo results
        logger.info(f"Loading Monte Carlo results from {input_csv}")
        results = load_mc_results(input_csv)

        # Aggregate by theta
        logger.info("Aggregating results by theta")
        aggregated = aggregate_by_theta(results)

        # Prepare final data structure
        logger.info("Preparing threshold identification data")
        final_data = prepare_threshold_data(aggregated)

        # Write output JSON
        logger.info(f"Writing output to {output_json}")
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, indent=2)

        logger.info(f"Successfully wrote {len(final_data['data'])} data points to {output_json}")

        # Log summary
        if final_data['data']:
            min_theta = final_data['data'][0]['theta']
            max_theta = final_data['data'][-1]['theta']
            min_prob = final_data['data'][0]['outlier_probability']
            max_prob = final_data['data'][-1]['outlier_probability']
            logger.info(f"Theta range: [{min_theta}, {max_theta}]")
            logger.info(f"Probability range: [{min_prob:.4f}, {max_prob:.4f}]")
            logger.info(f"Monotonicity check: {'PASS' if final_data['metadata']['monotonicity_check'] else 'WARN: Non-monotonic trend detected'}")

    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        logger.error("Ensure T021a (Monte Carlo runner) has completed and generated data/processed/mc_results.csv")
        raise
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        raise

if __name__ == '__main__':
    main()
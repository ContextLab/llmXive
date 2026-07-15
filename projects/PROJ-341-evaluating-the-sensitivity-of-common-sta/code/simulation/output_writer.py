"""
Output writer module for simulation results.
Handles writing raw p-values and loading them for downstream analysis.
"""
import os
import csv
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd

logger = get_logger(__name__)

def ensure_output_directory(output_path: str) -> None:
    """Ensure the directory for the output file exists."""
    directory = os.path.dirname(output_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Created output directory: {directory}")

def write_p_values_raw(results: List[Dict[str, Any]], output_path: str) -> None:
    """
    Write simulation results to a CSV file.

    Args:
        results: List of dictionaries containing simulation results.
                Expected keys: sample_size, effect_size, test_type, p_value, hypothesis_state
        output_path: Path to the output CSV file.
    """
    ensure_output_directory(output_path)

    if not results:
        logger.warning("No results to write. Creating empty CSV with headers.")
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'sample_size', 'effect_size', 'test_type', 'p_value', 'hypothesis_state'
            ])
            writer.writeheader()
        return

    # Normalize keys to ensure consistency
    normalized_results = []
    for r in results:
        normalized = {
            'sample_size': r.get('sample_size', r.get('n')),
            'effect_size': r.get('effect_size', 0.0),
            'test_type': r.get('test_type', r.get('test')),
            'p_value': r.get('p_value', r.get('p')),
            'hypothesis_state': r.get('hypothesis_state', r.get('hypothesis', 'H1'))
        }
        normalized_results.append(normalized)

    fieldnames = ['sample_size', 'effect_size', 'test_type', 'p_value', 'hypothesis_state']

    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(normalized_results)

    logger.info(f"Wrote {len(normalized_results)} results to {output_path}")

def load_p_values_raw(input_path: str) -> List[Dict[str, Any]]:
    """
    Load raw p-values from a CSV file.

    Args:
        input_path: Path to the input CSV file.

    Returns:
        List of dictionaries containing the loaded results.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_csv(input_path)
    results = df.to_dict(orient='records')
    logger.info(f"Loaded {len(results)} results from {input_path}")
    return results

def load_p_values_raw_safe(input_path: str) -> Optional[List[Dict[str, Any]]]:
    """
    Safely load raw p-values from a CSV file. Returns None if file not found or empty.

    Args:
        input_path: Path to the input CSV file.

    Returns:
        List of dictionaries or None if file doesn't exist or is empty.
    """
    if not os.path.exists(input_path):
        logger.warning(f"Input file not found: {input_path}")
        return None

    try:
        df = pd.read_csv(input_path)
        if df.empty:
            logger.warning(f"Input file is empty: {input_path}")
            return None
        results = df.to_dict(orient='records')
        logger.info(f"Loaded {len(results)} results from {input_path}")
        return results
    except Exception as e:
        logger.error(f"Error loading {input_path}: {e}")
        return None

def main():
    """
    Main function for testing the output writer.
    Generates sample results and writes them to the specified output path.
    """
    import argparse
    import numpy as np

    parser = argparse.ArgumentParser(description='Test the p-values output writer')
    parser.add_argument('--output', type=str, default='data/simulation/p_values_raw.csv',
                      help='Output CSV path')
    parser.add_argument('--n-samples', type=int, default=100,
                      help='Number of sample results to generate')
    parser.add_argument('--test-types', type=str, nargs='+', default=['t-test', 'anova', 'chi-squared'],
                      help='Test types to include')
    parser.add_argument('--effect-sizes', type=float, nargs='+', default=[0.0, 0.2, 0.5],
                      help='Effect sizes to include')
    parser.add_argument('--sample-sizes', type=int, nargs='+', default=[10, 30, 100],
                      help='Sample sizes to include')

    args = parser.parse_args()

    # Generate synthetic results for testing
    results = []
    np.random.seed(42)  # For reproducibility in test

    for n in args.sample_sizes:
        for effect in args.effect_sizes:
            for test_type in args.test_types:
                # Simulate a p-value (real simulation would compute this)
                # For testing, we generate a plausible p-value distribution
                if effect == 0.0:
                    # Null hypothesis true - uniform distribution
                    p_val = np.random.uniform(0, 1)
                    hypothesis = 'H0'
                else:
                    # Alternative hypothesis true - skewed towards low p-values
                    p_val = np.random.beta(1, 5) * (1 - effect * 0.5)
                    hypothesis = 'H1'

                results.append({
                    'sample_size': n,
                    'effect_size': effect,
                    'test_type': test_type,
                    'p_value': p_val,
                    'hypothesis_state': hypothesis
                })

    write_p_values_raw(results, args.output)
    print(f"Successfully wrote {len(results)} results to {args.output}")

if __name__ == '__main__':
    main()
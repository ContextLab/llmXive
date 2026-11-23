import os
import sys
import json
import logging
import numpy as np
from pathlib import Path
from typing import List, Dict, Any

from src.utils.config import get_global_seed
from src.utils.seeds import SeedManager

def generate_permutation_null_distribution(gap_sequence: List[float], num_permutations: int = 1000) -> List[float]:
    """
    Generates a null distribution of KS statistics by shuffling the gap sequence.

    Args:
        gap_sequence: A list of gap sizes.
        num_permutations: The number of permutations to generate.

    Returns:
        A list of KS statistics.
    """
    ks_statistics = []
    seed_manager = SeedManager()
    for _ in range(num_permutations):
        np.random.shuffle(gap_sequence)
        ks_statistic = np.max(np.abs(np.cumsum(gap_sequence) / len(gap_sequence) - np.linspace(0, 1, len(gap_sequence))))
        ks_statistics.append(ks_statistic)
    return ks_statistics

def run_pipeline(gap_sequence_path: str, output_path: str, num_permutations: int = 1000):
    """
    Runs the permutation test pipeline.

    Args:
        gap_sequence_path: Path to the file containing the gap sequence.
        output_path: Path to the output file for the null distribution.
        num_permutations: The number of permutations to generate.
    """
    try:
        with open(gap_sequence_path, 'r') as f:
            gap_sequence = [float(x) for x in f.read().split(',')]
    except FileNotFoundError:
        logging.error(f"Gap sequence file not found: {gap_sequence_path}")
        sys.exit(1)

    null_distribution = generate_permutation_null_distribution(gap_sequence, num_permutations)

    with open(output_path, 'w') as f:
        json.dump(null_distribution, f)

    logging.info(f"Permutation null distribution saved to: {output_path}")

def main():
    """
    Main function.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Default values
    gap_sequence_path = "data/processed/normalized_gaps.csv"
    output_path = "results/permutation_null_distribution.json"
    num_permutations = 1000

    # Run the pipeline
    run_pipeline(gap_sequence_path, output_path, num_permutations)

if __name__ == "__main__":
    main()
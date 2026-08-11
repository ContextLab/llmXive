"""
Feature Engineering for Integer Partition Analysis.

This module computes residual errors and generates statistical features
based on prime density and oscillatory patterns to model the deviation
between exact partition counts and the asymptotic baseline.
"""

import os
import csv
import math
import numpy as np
from typing import List, Tuple, Dict, Optional
import sys

# Add parent directory to path for imports if running as script
if __package__ is None or __package__ == '':
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
else:
    # Relative import for package usage
    pass

from utils.prime_sieve import generate_primes, get_prime_sieve
from utils.asymptotic_baseline import compute_asymptotic_baseline


def load_partition_data(filepath: str) -> List[Dict]:
    """
    Load partition data from a CSV file.

    Args:
        filepath: Path to the CSV file (e.g., data/raw/partitions_raw.csv).

    Returns:
        List of dictionaries containing n, p_P(n), and Q_as(n).
    """
    data = []
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Data file not found: {filepath}")

    with open(filepath, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({
                'n': int(row['n']),
                'p_P_n': int(row['p_P(n)']),
                'Q_as_n': float(row['Q_as(n)'])
            })
    return data


def get_prime_sieve_and_primes(n_max: int) -> Tuple[np.ndarray, List[int]]:
    """
    Generate the prime sieve and list of primes up to n_max.

    Args:
        n_max: Maximum value for n.

    Returns:
        Tuple of (boolean sieve array, list of primes).
    """
    sieve = get_prime_sieve(n_max)
    primes = generate_primes(n_max)
    return sieve, primes


def find_nearest_prime_distance(n: int, primes: List[int]) -> int:
    """
    Find the absolute distance to the nearest prime for a given n.

    Args:
        n: The integer to check.
        primes: Sorted list of primes.

    Returns:
        Absolute difference to the closest prime.
    """
    if n <= 1:
        return 1 - 2 if len(primes) > 0 and primes[0] == 2 else abs(n - 2) # Fallback

    # Binary search for insertion point
    import bisect
    idx = bisect.bisect_left(primes, n)

    min_dist = float('inf')

    # Check prime at idx (if within bounds)
    if idx < len(primes):
        min_dist = min(min_dist, abs(primes[idx] - n))

    # Check prime at idx - 1 (if within bounds)
    if idx > 0:
        min_dist = min(min_dist, abs(primes[idx - 1] - n))

    return int(min_dist)


def compute_features(data: List[Dict], sieve: np.ndarray, primes: List[int]) -> List[Dict]:
    """
    Compute residual error and additional features for each data point.

    Features:
        - R(n): Residual log error = log(p_P(n)) - log(Q_as(n))
        - pi_n: Prime counting function value (count of primes <= n)
        - inv_log_n: 1 / ln(n)
        - dist_nearest_prime: Distance to nearest prime
        - sin_log_n: sin(log(n))
        - cos_log_n: cos(log(n))

    Args:
        data: List of partition data dictionaries.
        sieve: Boolean array indicating primes.
        primes: List of prime numbers.

    Returns:
        List of dictionaries with original and computed features.
    """
    features = []
    for row in data:
        n = row['n']
        p_P_n = row['p_P_n']
        Q_as_n = row['Q_as_n']

        # Skip invalid entries where log would be undefined or zero
        if p_P_n <= 0 or Q_as_n <= 0:
            continue

        # Compute Residual R(n)
        # R(n) = log(p_P(n)) - log(Q_as(n))
        log_p = math.log(p_P_n)
        log_q = math.log(Q_as_n)
        R_n = log_p - log_q

        # Prime counting function pi(n)
        # Count primes <= n using the sieve or bisect
        # Since primes list is sorted, we can use bisect_right
        import bisect
        pi_n = bisect.bisect_right(primes, n)

        # 1 / ln(n)
        inv_log_n = 1.0 / math.log(n) if n > 1 else 0.0

        # Distance to nearest prime
        dist_nearest = find_nearest_prime_distance(n, primes)

        # Oscillatory features
        sin_log_n = math.sin(math.log(n))
        cos_log_n = math.cos(math.log(n))

        features.append({
            'n': n,
            'p_P_n': p_P_n,
            'Q_as_n': Q_as_n,
            'R_n': R_n,
            'pi_n': pi_n,
            'inv_log_n': inv_log_n,
            'dist_nearest_prime': dist_nearest,
            'sin_log_n': sin_log_n,
            'cos_log_n': cos_log_n
        })

    return features


def save_features(features: List[Dict], filepath: str) -> None:
    """
    Save computed features to a CSV file.

    Args:
        features: List of feature dictionaries.
        filepath: Output path for the CSV file.
    """
    if not features:
        raise ValueError("No features to save.")

    # Ensure directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    fieldnames = [
        'n', 'p_P_n', 'Q_as_n', 'R_n', 'pi_n', 'inv_log_n',
        'dist_nearest_prime', 'sin_log_n', 'cos_log_n'
    ]

    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(features)


def main():
    """
    Main entry point for feature engineering pipeline.
    """
    # Configuration
    input_path = 'data/raw/partitions_raw.csv'
    output_path = 'data/processed/features.csv'
    n_max = 50000

    print(f"Loading partition data from {input_path}...")
    try:
        data = load_partition_data(input_path)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    print(f"Loaded {len(data)} records.")

    print(f"Generating prime sieve up to {n_max}...")
    sieve, primes = get_prime_sieve_and_primes(n_max)
    print(f"Found {len(primes)} primes.")

    print("Computing features...")
    features = compute_features(data, sieve, primes)
    print(f"Computed features for {len(features)} valid records.")

    print(f"Saving features to {output_path}...")
    save_features(features, output_path)
    print("Done.")

    # Verification
    if os.path.exists(output_path):
        print(f"Output file created: {output_path}")
        # Quick check for required columns
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            first_row = next(reader)
            required_cols = ['dist_nearest_prime', 'sin_log_n', 'cos_log_n']
            missing = [col for col in required_cols if col not in first_row]
            if missing:
                print(f"WARNING: Missing columns in output: {missing}")
            else:
                print("Verification passed: All required columns present.")
    else:
        print("ERROR: Output file was not created.")
        sys.exit(1)


if __name__ == '__main__':
    main()
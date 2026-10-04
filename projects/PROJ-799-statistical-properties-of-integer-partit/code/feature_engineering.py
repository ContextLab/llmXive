"""
Feature Engineering for Integer Partitions into Distinct Prime Summands.

This module computes features based on prime density and gaps to model the
residual error R(n) = log(p_P(n)) - log(Q_as(n)).

It implements the distinct-prime generating function logic and explicitly
handles the "holes" created by prime gaps as per the project's theoretical
justification (T018, T040).
"""
import os
import csv
import math
import numpy as np
from typing import List, Tuple, Dict, Optional

from utils.prime_sieve import generate_primes, get_prime_sieve
from utils.asymptotic_baseline import compute_asymptotic_baseline

# Constants
DEFAULT_INPUT_PATH = "data/raw/partitions_raw.csv"
DEFAULT_OUTPUT_PATH = "data/processed/features.csv"
DEFAULT_N_MAX = 50000

def load_partition_data(filepath: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Load partition data from a CSV file.

    Args:
        filepath: Path to the CSV file containing n, p_P(n), Q_as(n).

    Returns:
        Tuple of (n_values, p_P_n, Q_as_n) as numpy arrays.
    """
    n_values = []
    p_P_n = []
    Q_as_n = []

    with open(filepath, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                n = int(row['n'])
                p_p = int(row['p_P(n)'])
                q_as = float(row['Q_as(n)'])
                n_values.append(n)
                p_P_n.append(p_p)
                Q_as_n.append(q_as)
            except (ValueError, KeyError) as e:
                # Skip malformed rows but log a warning in a real system
                continue

    return np.array(n_values, dtype=np.int32), np.array(p_P_n, dtype=np.int64), np.array(Q_as_n, dtype=np.float64)

def get_prime_sieve_and_primes(n_max: int) -> Tuple[np.ndarray, List[int]]:
    """
    Generate prime sieve and list of primes up to n_max.

    Args:
        n_max: Upper bound for prime generation.

    Returns:
        Tuple of (sieve_array, primes_list).
    """
    # Ensure we have enough primes for gap calculations (next prime might be > n_max)
    # We generate primes up to n_max + a small buffer to handle "next prime" for n near n_max
    # A safe buffer is the maximum expected gap, but for n=50000, max gap is small (~100).
    # We'll generate up to n_max + 200 to be safe.
    limit = n_max + 200
    sieve, primes = generate_primes(limit)
    return sieve, primes

def find_next_prime(n: int, primes: List[int]) -> int:
    """
    Find the smallest prime strictly greater than n using binary search.

    Args:
        n: The integer to search after.
        primes: Sorted list of precomputed primes.

    Returns:
        The next prime > n.
    """
    # Use binary search to find insertion point
    idx = np.searchsorted(primes, n, side='right')
    if idx < len(primes):
        return primes[idx]
    else:
        # Fallback: should not happen if primes array is large enough
        # This would require on-the-fly generation, but we precompute with buffer
        raise ValueError(f"No next prime found for {n} within precomputed range.")

def find_prev_prime(n: int, primes: List[int]) -> int:
    """
    Find the largest prime strictly less than n using binary search.

    Args:
        n: The integer to search before.
        primes: Sorted list of precomputed primes.

    Returns:
        The previous prime < n.
    """
    # Use binary search to find insertion point
    idx = np.searchsorted(primes, n, side='left')
    if idx > 0:
        return primes[idx - 1]
    else:
        # No prime less than n (n < 2)
        return -1

def is_prime_on_fly(n: int, sieve: np.ndarray) -> bool:
    """
    Check if n is prime using the precomputed sieve.

    Args:
        n: The integer to check.
        sieve: Boolean array where sieve[i] is True if i is prime.

    Returns:
        True if n is prime, False otherwise.
    """
    if n < 0 or n >= len(sieve):
        return False
    return bool(sieve[n])

def compute_prime_gap_size(n: int, primes: List[int], sieve: np.ndarray) -> float:
    """
    Calculate the prime gap size relevant to n.

    Logic:
      - If n is prime: Calculate the distance to the *next* prime (gap initiated by n).
      - If n is composite: Calculate the distance between the *next* prime and the *previous* prime (gap containing n).

    Args:
        n: The integer.
        primes: Sorted list of precomputed primes.
        sieve: Boolean array for primality check.

    Returns:
        The gap size as a float.
    """
    if is_prime_on_fly(n, sieve):
        # n is prime: distance to next prime
        next_p = find_next_prime(n, primes)
        return float(next_p - n)
    else:
        # n is composite: gap containing n
        prev_p = find_prev_prime(n, primes)
        next_p = find_next_prime(n, primes)
        if prev_p == -1:
            # n < 2, no previous prime. Treat as gap from 2 to next?
            # For n < 2, this is an edge case. Return next_p - 2 or 0?
            # Spec says "distance between next and previous". If no previous, undefined.
            # We'll return a large value or handle as 0. Given n starts at 1, let's return next_p - 2 (gap from 2)
            # Actually, for n=1, next prime is 2. Gap is 2-2=0? No, gap is between primes.
            # Let's return next_p - 2 if prev is missing, assuming gap starts at 2.
            # But strictly, gap is p_{k+1} - p_k. If n < 2, it's not in a gap between primes.
            # We'll return 0.0 for n < 2.
            return 0.0
        return float(next_p - prev_p)

def find_nearest_prime_distance(n: int, primes: List[int]) -> float:
    """
    Calculate the absolute distance to the closest prime (either smaller or larger).

    Args:
        n: The integer.
        primes: Sorted list of precomputed primes.

    Returns:
        The distance to the nearest prime.
    """
    # Use binary search to find insertion point
    idx = np.searchsorted(primes, n)

    # Check candidates: primes[idx] (next) and primes[idx-1] (prev)
    candidates = []
    if idx < len(primes):
        candidates.append(primes[idx] - n)
    if idx > 0:
        candidates.append(n - primes[idx - 1])

    if not candidates:
        return 0.0 # Should not happen for n >= 0 with valid primes

    return float(min(candidates))

def compute_features(n_values: np.ndarray, primes: List[int], sieve: np.ndarray) -> Dict[str, np.ndarray]:
    """
    Compute all required features for the given n values.

    Features:
      - pi_n: Prime counting function (density)
      - inv_log_n: 1 / ln(n)
      - distance_to_nearest_prime: Distance to closest prime
      - prime_gap_size: Gap size logic as defined
      - sin_log_n: sin(log(n))
      - cos_log_n: cos(log(n))
      - R_n: Residual error log(p_P(n)) - log(Q_as(n))

    Args:
        n_values: Array of n values.
        primes: List of precomputed primes.
        sieve: Boolean sieve array.

    Returns:
        Dictionary of feature arrays.
    """
    n_float = n_values.astype(np.float64)

    # 1. Prime Density (pi(n))
    # We need pi(n) for each n. Since we have primes list, we can use searchsorted.
    pi_n = np.searchsorted(primes, n_values, side='right').astype(np.float64)

    # 2. 1 / ln(n)
    # Handle n=0 or n=1 where log is undefined or zero
    inv_log_n = np.zeros_like(n_float)
    valid_indices = n_float > 1
    inv_log_n[valid_indices] = 1.0 / np.log(n_float[valid_indices])

    # 3. Distance to nearest prime
    distance_to_nearest_prime = np.array([find_nearest_prime_distance(n, primes) for n in n_values])

    # 4. Prime gap size
    prime_gap_size = np.array([compute_prime_gap_size(n, primes, sieve) for n in n_values])

    # 5. Oscillatory features
    sin_log_n = np.sin(np.log(n_float + 1e-9)) # Add epsilon to avoid log(0)
    cos_log_n = np.cos(np.log(n_float + 1e-9))

    return {
        'n': n_values,
        'pi_n': pi_n,
        'inv_log_n': inv_log_n,
        'distance_to_nearest_prime': distance_to_nearest_prime,
        'prime_gap_size': prime_gap_size,
        'sin_log_n': sin_log_n,
        'cos_log_n': cos_log_n
    }

def save_features(features: Dict[str, np.ndarray], filepath: str):
    """
    Save features to a CSV file.

    Args:
        features: Dictionary of feature arrays.
        filepath: Output path.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    fieldnames = [
        'n', 'pi_n', 'inv_log_n', 'distance_to_nearest_prime',
        'prime_gap_size', 'sin_log_n', 'cos_log_n'
    ]

    # Ensure all arrays have same length
    length = len(features['n'])
    for key, arr in features.items():
        if len(arr) != length:
            raise ValueError(f"Feature {key} has length {len(arr)}, expected {length}")

    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for i in range(length):
            row = {key: val[i] for key, val in features.items()}
            writer.writerow(row)

def main():
    """
    Main entry point for feature engineering.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Compute features for partition analysis.")
    parser.add_argument("--input", type=str, default=DEFAULT_INPUT_PATH,
                        help=f"Path to input CSV (default: {DEFAULT_INPUT_PATH})")
    parser.add_argument("--output", type=str, default=DEFAULT_OUTPUT_PATH,
                        help=f"Path to output CSV (default: {DEFAULT_OUTPUT_PATH})")
    parser.add_argument("--n-max", type=int, default=DEFAULT_N_MAX,
                        help=f"Maximum n to consider (default: {DEFAULT_N_MAX})")

    args = parser.parse_args()

    print(f"Loading partition data from {args.input}...")
    if not os.path.exists(args.input):
        raise FileNotFoundError(f"Input file not found: {args.input}")

    n_values, p_P_n, Q_as_n = load_partition_data(args.input)

    # Filter valid rows: n >= 5, p_P(n) > 0, Q_as(n) > 0
    # The spec explicitly requires excluding n < 5 and non-positive counts.
    valid_mask = (n_values >= 5) & (p_P_n > 0) & (Q_as_n > 0)

    n_filtered = n_values[valid_mask]
    p_P_filtered = p_P_n[valid_mask]
    Q_as_filtered = Q_as_n[valid_mask]

    print(f"Loaded {len(n_values)} rows, keeping {len(n_filtered)} valid rows.")

    if len(n_filtered) == 0:
        raise ValueError("No valid data rows after filtering. Check input data.")

    # Compute Residual R(n)
    # R(n) = log(p_P(n)) - log(Q_as(n))
    # Since we filtered Q_as > 0 and p_P > 0, log is safe.
    R_n = np.log(p_P_filtered) - np.log(Q_as_filtered)

    # Get primes and sieve
    # We need primes up to at least max(n) + buffer for gap calculation
    max_n = int(np.max(n_filtered))
    sieve, primes = get_prime_sieve_and_primes(max_n)

    # Compute features
    print("Computing features...")
    features = compute_features(n_filtered, primes, sieve)

    # Add R_n to features
    features['R_n'] = R_n

    # Re-order for saving (put R_n at end or specific spot)
    # We'll keep the order defined in compute_features + R_n
    # Actually, let's define a specific order for output
    output_order = [
        'n', 'pi_n', 'inv_log_n', 'distance_to_nearest_prime',
        'prime_gap_size', 'sin_log_n', 'cos_log_n', 'R_n'
    ]

    # Construct ordered dict for saving
    ordered_features = {k: features[k] for k in output_order if k in features}

    # Save
    print(f"Saving features to {args.output}...")
    save_features(ordered_features, args.output)

    print(f"Feature engineering complete. Output saved to {args.output}")

if __name__ == "__main__":
    main()
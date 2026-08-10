"""
Feature Engineering for Integer Partition Residuals.

This module computes residual errors R(n) = log(p_P(n)) - log(Q_as(n)) and
generates predictive features including prime density metrics and oscillatory terms.

Features generated:
- pi_n: Prime counting function pi(n)
- inv_log_n: 1 / ln(n)
- dist_nearest_prime: Absolute distance to the nearest prime
- sin_log_n: sin(log(n))
- cos_log_n: cos(log(n))

Output: data/processed/features.csv
"""

import os
import csv
import math
import numpy as np
from typing import List, Tuple, Dict

# Add project root to path to allow relative imports if run as script
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.prime_sieve import get_prime_sieve
from utils.asymptotic_baseline import compute_asymptotic_baseline


def load_partition_data(input_path: str) -> List[Dict]:
    """
    Load partition data from CSV.
    Expects columns: n, p_P(n), Q_as(n)
    """
    data = []
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({
                'n': int(row['n']),
                'p_P_n': int(row['p_P(n)']),
                'Q_as_n': float(row['Q_as(n)'])
            })
    return data


def get_prime_sieve_and_primes(max_n: int) -> Tuple[np.ndarray, List[int]]:
    """
    Retrieve the boolean sieve array and the list of primes.
    Uses the precomputed sieve from utils.prime_sieve.
    """
    sieve, primes = get_prime_sieve(max_n)
    return sieve, primes


def find_nearest_prime_distance(n: int, primes: List[int], sieve: np.ndarray) -> int:
    """
    Calculate the absolute distance from n to the nearest prime.
    Checks n itself, then expands outwards (n-1, n+1, n-2, n+2, ...).
    """
    if n < 2:
        # For n=0,1, the nearest prime is 2. Distance is 2-0=2 or 2-1=1.
        # Since 2 is the smallest prime.
        return 2 - n if n <= 2 else 0 # n=0->2, n=1->1, n=2->0 (handled by loop)

    # Check if n is prime
    if n < len(sieve) and sieve[n]:
        return 0

    # Expand search
    # We need to be careful with bounds if n is near max_n
    # But since we generate up to max_n, and n <= max_n, we check upwards
    # If n is max_n, we might need to check beyond, but typically we assume
    # the nearest prime is within reasonable range or we have primes list.
    
    # Use the primes list for binary search or simple iteration since primes are sorted
    # Binary search for insertion point
    import bisect
    idx = bisect.bisect_left(primes, n)
    
    dist = float('inf')
    
    # Check prime at idx (>= n)
    if idx < len(primes):
        dist = min(dist, primes[idx] - n)
    
    # Check prime at idx-1 (< n)
    if idx > 0:
        dist = min(dist, n - primes[idx-1])
    
    return int(dist)


def compute_features(data: List[Dict], sieve: np.ndarray, primes: List[int]) -> List[Dict]:
    """
    Compute features for each partition record.
    Filters out records where p_P(n) == 0 or Q_as(n) <= 0 to avoid log(0).
    """
    features = []
    
    for row in data:
        n = row['n']
        p_p_n = row['p_P_n']
        q_as_n = row['Q_as_n']
        
        # Skip invalid entries for log calculation
        if p_p_n == 0 or q_as_n <= 0:
            continue
        
        # Compute Residual R(n)
        log_p = math.log(p_p_n)
        log_q = math.log(q_as_n)
        r_n = log_p - log_q
        
        # Feature: pi(n)
        # pi(n) is the count of primes <= n.
        # Since primes list is sorted, we can use bisect
        import bisect
        pi_n = bisect.bisect_right(primes, n)
        
        # Feature: 1 / ln(n)
        inv_log_n = 1.0 / math.log(n) if n > 1 else 0.0
        
        # Feature: Distance to nearest prime
        dist_nearest = find_nearest_prime_distance(n, primes, sieve)
        
        # Oscillatory features
        sin_log_n = math.sin(math.log(n))
        cos_log_n = math.cos(math.log(n))
        
        features.append({
            'n': n,
            'p_P_n': p_p_n,
            'Q_as_n': q_as_n,
            'R_n': r_n,
            'pi_n': pi_n,
            'inv_log_n': inv_log_n,
            'dist_nearest_prime': dist_nearest,
            'sin_log_n': sin_log_n,
            'cos_log_n': cos_log_n
        })
    
    return features


def save_features(features: List[Dict], output_path: str):
    """
    Save computed features to CSV.
    """
    if not features:
        raise ValueError("No features computed to save.")
    
    fieldnames = [
        'n', 'p_P_n', 'Q_as_n', 'R_n', 
        'pi_n', 'inv_log_n', 'dist_nearest_prime', 
        'sin_log_n', 'cos_log_n'
    ]
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(features)


def main():
    # Configuration
    input_path = 'data/raw/partitions_raw.csv'
    output_path = 'data/processed/features.csv'
    
    # Determine max_n from input file to size sieve appropriately
    # We assume the input file has the max n in the first column or we can scan
    # For efficiency, we'll just load the sieve for a safe upper bound or scan the file first.
    # Since we need the sieve for distance calculation, let's assume we know max_n or scan.
    # Scanning is safer.
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
        
    # Scan for max_n
    max_n = 0
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            n_val = int(row['n'])
            if n_val > max_n:
                max_n = n_val
    
    print(f"Detected max_n: {max_n}")
    
    # Load Sieve and Primes
    print("Loading prime sieve...")
    sieve, primes = get_prime_sieve_and_primes(max_n)
    
    # Load Data
    print("Loading partition data...")
    data = load_partition_data(input_path)
    print(f"Loaded {len(data)} records.")
    
    # Compute Features
    print("Computing features...")
    features = compute_features(data, sieve, primes)
    print(f"Computed features for {len(features)} valid records.")
    
    # Save
    print(f"Saving features to {output_path}...")
    save_features(features, output_path)
    print("Done.")


if __name__ == '__main__':
    main()
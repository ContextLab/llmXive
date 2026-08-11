"""
Generate reference values for p_P(n): partitions of n into distinct prime summands.

This script computes exact counts for n in [1, 100] using dynamic programming
based on the generating function:
    \\prod_{p \\in \\mathbb{P}} (1 + q^p)

The algorithm iterates over primes (from T004) and updates a 1D DP array where
dp[n] represents the number of ways to partition n into distinct primes.
The order of loops (outer: primes, inner: descending n) ensures each prime
is used at most once per partition.

Output: tests/data/reference_values.csv with columns: n, p_P(n)
"""
import os
import csv
import numpy as np
from utils.prime_sieve import generate_primes

# Configuration
N_MAX = 100
OUTPUT_PATH = "tests/data/reference_values.csv"

def generate_reference_values(n_max: int) -> np.ndarray:
    """
    Compute exact p_P(n) for n in [0, n_max] using DP.

    dp[n] = number of partitions of n into distinct primes.
    Generating function: \\prod_{p} (1 + q^p)
    """
    # Get primes up to n_max (only primes <= n_max can contribute to partitions of n <= n_max)
    primes = generate_primes(n_max)
    
    # Initialize DP array: dp[0] = 1 (one way to partition 0: empty set), others 0
    dp = np.zeros(n_max + 1, dtype=np.int64)
    dp[0] = 1
    
    # Iterate over each prime and update DP table
    # Descending order ensures each prime is used at most once (distinct constraint)
    for p in primes:
        for n in range(n_max, p - 1, -1):
            dp[n] += dp[n - p]
    
    return dp

def main():
    """Generate reference values and save to CSV."""
    # Ensure output directory exists
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    
    # Compute reference values
    print(f"Generating reference values for n in [1, {N_MAX}]...")
    dp = generate_reference_values(N_MAX)
    
    # Write to CSV
    with open(OUTPUT_PATH, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['n', 'p_P(n)'])
        for n in range(1, N_MAX + 1):
            writer.writerow([n, int(dp[n])])
    
    print(f"Reference values saved to {OUTPUT_PATH}")
    print(f"Sample values: n=10 -> {dp[10]}, n=50 -> {dp[50]}, n=100 -> {dp[100]}")

if __name__ == "__main__":
    main()

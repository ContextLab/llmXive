import os
import csv
import math
import numpy as np
from typing import List, Tuple, Dict, Optional
import sys

# Import from sibling modules as per API surface
# Assuming these are available in the project structure:
# from utils.prime_sieve import generate_primes, get_prime_sieve
# However, to be self-contained and robust for this task, we will implement
# the necessary prime generation logic or import if the API surface allows.
# The API surface shows `from utils.prime_sieve import get_prime_sieve, generate_primes`.

def load_partition_data(filepath: str) -> Tuple[List[int], List[int], List[float]]:
    """
    Load partition data from CSV.
    Returns: n_values, p_P_n, Q_as_n
    """
    n_values = []
    p_P_n = []
    Q_as_n = []
    
    with open(filepath, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            n = int(row['n'])
            p_val = int(row['p_P(n)'])
            q_val = float(row['Q_as(n)'])
            n_values.append(n)
            p_P_n.append(p_val)
            Q_as_n.append(q_val)
    
    return n_values, p_P_n, Q_as_n

def get_prime_sieve_and_primes(limit: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate sieve and primes up to limit.
    Returns: sieve (bool array), primes (int32 array)
    """
    # Implement Sieve of Eratosthenes
    sieve = np.ones(limit + 1, dtype=bool)
    sieve[0] = False
    sieve[1] = False
    for i in range(2, int(limit**0.5) + 1):
        if sieve[i]:
            sieve[i*i:limit+1:i] = False
    
    primes = np.nonzero(sieve)[0].astype(np.int32)
    return sieve, primes

def find_nearest_prime_distance(n: int, primes: np.ndarray, sieve: np.ndarray) -> int:
    """
    Find the absolute distance to the nearest prime (smaller or larger).
    Uses binary search on the sorted primes array.
    """
    if n <= 1:
        return 1  # Distance to 2
    
    # Use searchsorted to find insertion point
    idx = np.searchsorted(primes, n)
    
    # Check bounds
    if idx == 0:
        return int(primes[0] - n)
    if idx >= len(primes):
        # n is larger than all precomputed primes
        # Fallback: return distance to the largest known prime
        # This handles the edge case where next prime is out of range
        return int(n - primes[-1])
    
    # n is between primes[idx-1] and primes[idx]
    lower_prime = primes[idx-1]
    upper_prime = primes[idx]
    
    dist_lower = int(n - lower_prime)
    dist_upper = int(upper_prime - n)
    
    return min(dist_lower, dist_upper)

def find_next_prime(n: int, primes: np.ndarray, sieve: np.ndarray) -> Optional[int]:
    """
    Find the next prime strictly greater than n.
    If n is prime, returns the next prime after n.
    If the next prime is outside the sieve range, returns None (truncation).
    """
    # Find insertion point for n
    idx = np.searchsorted(primes, n)
    
    # If n is in primes, idx points to n. We want the next one.
    # If n is not in primes, idx points to the first prime > n.
    if idx < len(primes):
        if primes[idx] == n:
            if idx + 1 < len(primes):
                return int(primes[idx+1])
            else:
                return None # No next prime in sieve
        else:
            return int(primes[idx])
    else:
        return None # No primes > n in sieve

def find_prev_prime(n: int, primes: np.ndarray) -> Optional[int]:
    """
    Find the previous prime strictly smaller than n.
    """
    idx = np.searchsorted(primes, n)
    if idx == 0:
        return None
    if primes[idx-1] == n:
        if idx - 2 >= 0:
            return int(primes[idx-2])
        else:
            return None
    else:
        return int(primes[idx-1])

def compute_prime_gap_size(n: int, primes: np.ndarray, sieve: np.ndarray) -> int:
    """
    Calculate 'prime_gap_size' with robust logic for edge cases.
    
    Logic:
    - If n is prime: Calculate distance to the *next* prime (gap initiated by n).
    - If n is composite: Calculate distance between *next* and *previous* primes (gap containing n).
    
    Fallback for upper bound:
    - If the required prime (next or prev) is not in the precomputed sieve,
      we explicitly document this truncation.
      For the 'next prime' case (n is prime or we need upper bound), if it's missing,
      we cannot compute the full gap. We return a sentinel or handle gracefully.
      Per task requirements: "Implement a fallback to generate the next prime on-the-fly 
      if necessary, or explicitly document the truncation error".
      
      Since generating primes on-the-fly beyond 50k is expensive and might violate 
      memory/time constraints if done repeatedly, and the task mentions "truncation error",
      we will return a specific value indicating truncation or handle it by 
      estimating the gap based on the last known gap if strictly necessary, 
      BUT the prompt says "fallback to generate... OR document truncation".
      
      Given the constraints of a research pipeline, returning a robust value 
      that doesn't crash is preferred. If the next prime is missing, we can't 
      calculate the exact gap. However, for the purpose of the regression model,
      a value of -1 or a large number might be misleading.
      
      Strategy: If the next prime is missing, we return the distance to the 
      last known prime as a lower bound for the gap (if n is composite) or 
      simply return the distance to the last prime (if n is prime, gap is unknown).
      However, the most honest approach for "truncation error" is to flag it.
      
      Let's implement a fallback: If the next prime is not found, we attempt 
      to generate the next prime using a simple trial division (on-the-fly) 
      ONLY if n is near the boundary. If that fails or is too slow, we return 
      a sentinel value (e.g., -1) which the downstream model should handle, 
      OR we document that the feature is truncated.
      
      Re-reading task: "Implement a fallback to generate the next prime on-the-fly 
      if necessary".
      
      We will implement a simple `next_prime_on_the_fly` function.
    """
    
    is_n_prime = (n < len(sieve)) and sieve[n]
    
    if is_n_prime:
        # n is prime: distance to NEXT prime
        next_p = find_next_prime(n, primes, sieve)
        if next_p is not None:
            return int(next_p - n)
        else:
            # Fallback: Generate next prime on the fly
            candidate = n + 2
            while True:
                if is_prime_on_fly(candidate, primes):
                    return int(candidate - n)
                candidate += 2
    else:
        # n is composite: distance between NEXT and PREVIOUS primes
        next_p = find_next_prime(n, primes, sieve)
        prev_p = find_prev_prime(n, primes)
        
        if next_p is not None and prev_p is not None:
            return int(next_p - prev_p)
        elif next_p is None and prev_p is not None:
            # Try to find next prime on the fly
            candidate = n + 2
            while candidate <= n + 10000: # Limit search to avoid infinite loop
                if is_prime_on_fly(candidate, primes):
                    return int(candidate - prev_p)
                candidate += 2
            # If still not found, return distance to last prime as a proxy? 
            # Or return -1. Let's return distance to last prime to avoid NaN, 
            # but this is a truncation artifact.
            return int(n - prev_p) # This is a lower bound of the gap
        elif next_p is not None and prev_p is None:
            # Should not happen for n > 2
            return int(next_p - n)
        else:
            # Both missing? n is very small or very large?
            return 0

def is_prime_on_fly(n: int, known_primes: np.ndarray) -> bool:
    """
    Check if n is prime using trial division by known primes.
    """
    if n < 2:
        return False
    # Check against known primes up to sqrt(n)
    limit = int(math.sqrt(n)) + 1
    for p in known_primes:
        if p > limit:
            break
        if n % p == 0:
            return False
    return True

def compute_features(n_values: List[int], p_P_n: List[int], Q_as_n: List[float], 
                     primes: np.ndarray, sieve: np.ndarray) -> List[Dict]:
    """
    Compute all features for the regression model.
    """
    features = []
    
    for i, n in enumerate(n_values):
        p_val = p_P_n[i]
        q_val = Q_as_n[i]
        
        # Skip invalid rows
        if p_val <= 0 or q_val <= 0:
            continue
        
        # Calculate Residual R(n)
        r_n = math.log(p_val) - math.log(q_val)
        
        # Compute features
        pi_n = np.searchsorted(primes, n) # Count of primes <= n
        
        # 1/ln(n)
        inv_log_n = 1.0 / math.log(n) if n > 1 else 0.0
        
        # Distance to nearest prime
        dist_nearest = find_nearest_prime_distance(n, primes, sieve)
        
        # Prime gap size (with fallback)
        gap_size = compute_prime_gap_size(n, primes, sieve)
        
        # Oscillatory features
        sin_log_n = math.sin(math.log(n))
        cos_log_n = math.cos(math.log(n))
        
        features.append({
            'n': n,
            'R_n': r_n,
            'pi_n': int(pi_n),
            'inv_log_n': inv_log_n,
            'distance_to_nearest_prime': dist_nearest,
            'prime_gap_size': gap_size,
            'sin_log_n': sin_log_n,
            'cos_log_n': cos_log_n
        })
        
    return features

def save_features(features: List[Dict], filepath: str):
    """
    Save features to CSV.
    """
    if not features:
        print("Warning: No features to save.")
        return
    
    fieldnames = features[0].keys()
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(features)

def main():
    """
    Main entry point for feature engineering.
    """
    # Paths
    input_path = "data/raw/partitions_raw.csv"
    output_path = "data/processed/features.csv"
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Load data
    print(f"Loading partition data from {input_path}...")
    n_values, p_P_n, Q_as_n = load_partition_data(input_path)
    print(f"Loaded {len(n_values)} records.")
    
    # Load/Generate Primes
    # We need primes up to the max n in the data, plus a buffer for gap calculation
    max_n = max(n_values)
    sieve_limit = max_n + 10000 # Buffer for next prime calculation
    print(f"Generating primes up to {sieve_limit}...")
    sieve, primes = get_prime_sieve_and_primes(sieve_limit)
    
    # Compute features
    print("Computing features...")
    features = compute_features(n_values, p_P_n, Q_as_n, primes, sieve)
    print(f"Computed {len(features)} feature rows.")
    
    # Save features
    print(f"Saving features to {output_path}...")
    save_features(features, output_path)
    print("Done.")

if __name__ == "__main__":
    main()
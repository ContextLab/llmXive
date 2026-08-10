from typing import List, Optional
import numpy as np
import os

def get_prime_sieve(limit: int) -> np.ndarray:
    """
    Generate a boolean sieve array up to `limit` using Sieve of Eratosthenes.
    Returns a boolean array where True indicates the index is prime.
    Uses memory-efficient boolean array (O(N) space).
    
    Parameters
    ----------
    limit : int
        The upper bound for prime generation (inclusive).
    
    Returns
    -------
    np.ndarray
        A boolean array of size `limit + 1` where index `i` is True if `i` is prime.
    """
    if limit < 2:
        return np.zeros(limit + 1, dtype=bool)
    
    # Initialize sieve: True means potentially prime
    sieve = np.ones(limit + 1, dtype=bool)
    sieve[0] = False
    sieve[1] = False
    
    # Iterate only up to sqrt(limit) for efficiency
    # Using integer arithmetic for the upper bound
    sqrt_limit = int(np.sqrt(limit))
    for i in range(2, sqrt_limit + 1):
        if sieve[i]:
            # Mark multiples of i starting from i*i
            # Slice assignment is vectorized and fast
            sieve[i*i : limit+1 : i] = False
    
    return sieve

def generate_primes(limit: int) -> List[int]:
    """
    Generate a list of all prime numbers up to `limit`.
    Uses the Sieve of Eratosthenes for efficiency.
    
    Parameters
    ----------
    limit : int
        The upper bound for prime generation (inclusive).
    
    Returns
    -------
    List[int]
        A list of prime numbers <= limit.
    """
    if limit < 2:
        return []
    
    sieve = get_prime_sieve(limit)
    # Extract indices where sieve is True
    return [i for i, is_prime in enumerate(sieve) if is_prime]

# Optional: Pre-compute sieve for the project's maximum n (50,000) + buffer
# This covers the requirement to find nearest neighbors for n=50,000.
# The buffer ensures we have primes > 50,000 for distance calculations.
PROJECT_N_MAX = 50000
SIEVE_BUFFER = 100
_PRIME_LIMIT = PROJECT_N_MAX + SIEVE_BUFFER

# Pre-computed prime list for the project scope
# Accessible via `generate_primes(_PRIME_LIMIT)` or cached if needed.
# To avoid global execution overhead on import, we provide a lazy getter if required,
# but for this task, the functions above are the primary API.

if __name__ == "__main__":
    """
    Main entry point for T004: Generate primes up to 50,000 and save to code/utils/primes.npy
    """
    # Define the limit as per task requirement
    limit = 50000
    
    # Generate primes
    primes = generate_primes(limit)
    
    # Convert to numpy array for efficient storage
    primes_array = np.array(primes, dtype=np.int64)
    
    # Determine output path relative to project root
    # The script is at code/utils/prime_sieve.py, output goes to code/utils/primes.npy
    output_path = os.path.join(os.path.dirname(__file__), "primes.npy")
    
    # Save to disk
    np.save(output_path, primes_array)
    
    print(f"Generated {len(primes)} primes up to {limit}.")
    print(f"Saved to: {output_path}")
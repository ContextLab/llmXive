from typing import List, Optional
import numpy as np
import os
import hashlib

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

def compute_sha256(filepath: str) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_state_file(checksum: str, output_path: str):
    """
    Update state/projects/PROJ-799.yaml with the checksum and timestamp.
    Creates the file if it doesn't exist.
    """
    import yaml
    from datetime import datetime, timezone

    state_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "state", "projects", "PROJ-799.yaml")
    
    # Ensure state directory exists
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    
    # Load existing state or initialize
    if os.path.exists(state_path):
        with open(state_path, 'r') as f:
            state = yaml.safe_load(f) or {}
    else:
        state = {}
    
    # Initialize keys if missing
    if 'artifact_hashes' not in state:
        state['artifact_hashes'] = {}
    
    # Update checksum and timestamp
    state['artifact_hashes']['primes_sieve'] = checksum
    state['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    # Write back
    with open(state_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

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
    # Task requires 1D np.int32 array
    primes_array = np.array(primes, dtype=np.int32)
    
    # Determine output path relative to project root
    # The script is at code/utils/prime_sieve.py, output goes to code/utils/primes.npy
    output_path = os.path.join(os.path.dirname(__file__), "primes.npy")
    
    # Save to disk
    np.save(output_path, primes_array)
    
    # Compute checksum
    checksum = compute_sha256(output_path)
    
    # Update state file
    update_state_file(checksum, output_path)
    
    print(f"Generated {len(primes)} primes up to {limit}.")
    print(f"Saved to: {output_path}")
    print(f"Array dtype: {primes_array.dtype}")
    print(f"Array shape: {primes_array.shape}")
    print(f"SHA-256 Checksum: {checksum}")
    print("Updated state/projects/PROJ-799.yaml")
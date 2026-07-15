"""
Prime Generation and Gap Analysis Pipeline.

Implements segmented sieve for memory-efficient prime generation up to N=10^10
and computes consecutive prime gaps, streaming results to CSV.
"""
import os
import math
import sys
from pathlib import Path
from typing import List, Generator, Tuple, Optional
import csv

# Ensure project root is in path for imports if run as script
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.utils.config import get_config
from src.utils.seeds import set_global_seed
from src.utils.io import compute_file_checksum
from src.utils.models import PrimeGap

def simple_sieve(limit: int) -> List[int]:
    """
    Simple Sieve of Eratosthenes for small limits.
    Returns a list of primes up to limit.
    """
    if limit < 2:
        return []
    sieve = bytearray([1]) * (limit + 1)
    sieve[0:2] = b'\x00\x00'
    for i in range(2, int(limit**0.5) + 1):
        if sieve[i]:
            sieve[i*i:limit+1:i] = b'\x00' * len(sieve[i*i:limit+1:i])
    return [i for i, is_prime in enumerate(sieve) if is_prime]

def segmented_sieve(n: int, segment_size: int = 1000000) -> Generator[List[int], None, None]:
    """
    Segmented Sieve of Eratosthenes.
    Yields chunks of primes up to n.
    """
    if n < 2:
        return

    # Precompute primes up to sqrt(n) for sieving
    sqrt_n = int(math.isqrt(n))
    base_primes = simple_sieve(sqrt_n)

    low = 0
    while low < n:
        high = min(low + segment_size, n)
        segment_size_actual = high - low
        segment = bytearray([1]) * segment_size_actual

        for p in base_primes:
            # Find the first multiple of p >= low
            start = max(p * p, ((low + p - 1) // p) * p)
            if start >= high:
                continue
            # Mark multiples
            start_idx = start - low
            segment[start_idx:segment_size_actual:p] = b'\x00' * len(segment[start_idx:segment_size_actual:p])

        # Collect primes in this segment
        chunk_primes = [low + i for i, is_prime in enumerate(segment) if is_prime]
        yield chunk_primes
        low = high

def compute_normalized_gap(prime_before: int, prime_after: int) -> float:
    """
    Compute the normalized gap size.
    Normalized gap = (prime_after - prime_before) / log(prime_before)^2
    per Cramér model prediction.
    """
    if prime_before <= 1:
        return float('inf')
    log_p = math.log(prime_before)
    if log_p == 0:
        return float('inf')
    return (prime_after - prime_before) / (log_p ** 2)

def run_pipeline(output_path: Optional[str] = None):
    """
    Main pipeline: Generate primes, compute gaps, stream to CSV.
    """
    config = get_config()
    N = config.get('N', 10**10)  # Default to 10^10 if not specified
    W = config.get('W', 10**6)
    
    # Use deterministic seed for reproducibility (though not strictly needed for sieve)
    set_global_seed(config.get('seed', 42))

    if output_path is None:
        output_path = str(Path("data/processed/primes_gaps.csv"))
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    print(f"Starting prime gap generation up to N={N}...")
    print(f"Output will be written to: {output_file}")

    last_prime = None
    count = 0
    
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # Write header
        writer.writerow(['prime_before', 'prime_after', 'gap_size', 'normalized_gap'])

        for chunk in segmented_sieve(N, segment_size=W):
            if not chunk:
                continue
            
            # Process the chunk
            if last_prime is not None:
                # Gap between last chunk's end and this chunk's start
                p_prev = last_prime
                p_curr = chunk[0]
                gap = p_curr - p_prev
                norm_gap = compute_normalized_gap(p_prev, p_curr)
                writer.writerow([p_prev, p_curr, gap, f"{norm_gap:.10f}"])
                count += 1

            # Gaps within the chunk
            for i in range(len(chunk) - 1):
                p_prev = chunk[i]
                p_curr = chunk[i+1]
                gap = p_curr - p_prev
                norm_gap = compute_normalized_gap(p_prev, p_curr)
                writer.writerow([p_prev, p_curr, gap, f"{norm_gap:.10f}"])
                count += 1

            last_prime = chunk[-1]
            
            if count % 1000000 == 0:
                print(f"Processed {count} gaps so far...")

    # Compute checksum
    checksum = compute_file_checksum(output_file)
    print(f"Pipeline complete. Total gaps: {count}")
    print(f"Output file: {output_file}")
    print(f"Checksum: {checksum}")
    
    return output_file

if __name__ == "__main__":
    # Run for a smaller N for testing if no args, else use config
    # For full run, ensure N in config is 10^10
    run_pipeline()

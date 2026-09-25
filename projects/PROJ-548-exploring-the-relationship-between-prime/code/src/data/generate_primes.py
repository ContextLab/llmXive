import os
import sys
import time
import csv
import logging
import math
from pathlib import Path

# Add project root to path for imports if running as script
_project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_project_root))

from src.utils.config import ensure_directories, get_global_seed
from src.utils.logging import get_logger

# Constants
N = 10**10
SEGMENT_SIZE = 10**7  # Process 10 million numbers at a time to manage memory
OUTPUT_FILE = "data/processed/raw_gaps.csv"

# Setup logging
logger = get_logger(__name__)

def simple_sieve(limit):
    """
    Generate primes up to limit using a simple sieve.
    Used only for small limits (segment boundaries).
    """
    if limit < 2:
        return []
    sieve = bytearray([1]) * (limit + 1)
    sieve[0] = 0
    sieve[1] = 0
    for i in range(2, int(limit**0.5) + 1):
        if sieve[i]:
            sieve[i*i:limit+1:i] = bytearray([0]) * len(range(i*i, limit+1, i))
    return [i for i, is_prime in enumerate(sieve) if is_prime]

def segmented_sieve(n, output_path):
    """
    Generate primes up to n using a segmented sieve to stay within memory limits.
    Computes consecutive prime gaps and streams them to a CSV file.
    
    Args:
        n (int): Upper bound for prime generation (N = 10^10).
        output_path (str): Path to the output CSV file.
    
    Returns:
        int: Total number of primes generated.
    """
    ensure_directories()
    
    logger.info(f"Starting segmented sieve up to {n}")
    logger.info(f"Segment size: {SEGMENT_SIZE}")
    logger.info(f"Output file: {output_path}")

    # Precompute primes up to sqrt(n) for sieving
    sqrt_n = int(math.isqrt(n))
    base_primes = simple_sieve(sqrt_n)
    logger.info(f"Base primes up to {sqrt_n}: {len(base_primes)}")

    # Open output file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    prev_prime = None
    gap_count = 0
    total_primes = 0
    
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['prime_before', 'prime_after', 'gap_size'])
        
        low = 2
        while low <= n:
            high = min(low + SEGMENT_SIZE - 1, n)
            logger.info(f"Processing segment [{low}, {high}]")
            
            # Initialize segment sieve
            segment_size = high - low + 1
            is_prime = bytearray([1]) * segment_size
            
            # Mark composites in the segment
            for p in base_primes:
                # Find the first multiple of p >= low
                start = max(p * p, ((low + p - 1) // p) * p)
                if start > high:
                    continue
                # Mark multiples
                start_idx = start - low
                is_prime[start_idx:segment_size:p] = bytearray([0]) * ((segment_size - 1 - start_idx) // p + 1)
            
            # Extract primes in this segment
            for i, is_p in enumerate(is_prime):
                if is_p:
                    current_prime = low + i
                    if current_prime > n:
                        break
                    
                    total_primes += 1
                    if prev_prime is not None:
                        gap = current_prime - prev_prime
                        writer.writerow([prev_prime, current_prime, gap])
                        gap_count += 1
                    prev_prime = current_prime
            
            low = high + 1
    
    logger.info(f"Segmented sieve completed. Total primes: {total_primes}, Total gaps: {gap_count}")
    return total_primes

def compute_normalized_gap(gap, prime):
    """
    Compute the normalized gap: gap / (log(p))^2
    Note: Normalization is handled in T018b, this is just a utility.
    """
    if prime <= 1:
        return 0.0
    log_p = math.log(prime)
    return gap / (log_p * log_p)

def run_pipeline():
    """
    Execute the prime generation and gap computation pipeline.
    Generates primes up to N=10^10 and writes gaps to data/processed/raw_gaps.csv.
    """
    start_time = time.time()
    try:
        total_primes = segmented_sieve(N, OUTPUT_FILE)
        elapsed = time.time() - start_time
        logger.info(f"Pipeline completed in {elapsed:.2f} seconds. Generated {total_primes} primes.")
        return True
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

def main():
    """
    Main entry point for the script.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Ensure global seed is set for reproducibility (though not used in deterministic sieve)
    get_global_seed()
    
    success = run_pipeline()
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
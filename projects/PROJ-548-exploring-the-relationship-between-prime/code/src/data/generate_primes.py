"""
Prime Generation and Gap Computation Pipeline.

Implements a segmented sieve to generate primes up to N=10^10 and computes
consecutive prime gaps, streaming results to a CSV file to ensure memory safety.

Addresses: FR-001 (Generate primes up to 10^10), SC-004 (Memory efficiency).
"""

import os
import sys
import time
import csv
import logging
import math
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.config import get_global_seed
from src.utils.io import update_state_checksums, load_state, save_state

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration Constants
# Target N as per FR-001
TARGET_N = 10**10
# Fallback N if runtime exceeds limits (SC-005)
FALLBACK_N = 10**9
# Chunk size for segmented sieve (adjustable for RAM constraints)
SEGMENT_SIZE = 10**6
# Output file paths
GAPS_OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "gaps.csv"
PRIMES_CACHE_PATH = PROJECT_ROOT / "data" / "raw" / "primes_segment_{}.csv"

# Ensure directories exist
def ensure_directories():
    """Create necessary directories for output."""
    dirs = [
        PROJECT_ROOT / "data" / "raw",
        PROJECT_ROOT / "data" / "processed",
        PROJECT_ROOT / "results",
        PROJECT_ROOT / "state"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directories: {dirs}")

def simple_sieve(limit):
    """
    Simple Sieve of Eratosthenes for small limits.
    Returns a list of primes up to `limit`.
    """
    if limit < 2:
        return []
    sieve = bytearray([1]) * (limit + 1)
    sieve[0] = sieve[1] = 0
    for i in range(2, int(math.sqrt(limit)) + 1):
        if sieve[i]:
            sieve[i*i : limit+1 : i] = bytearray([0]) * len(range(i*i, limit+1, i))
    return [i for i, is_prime in enumerate(sieve) if is_prime]

def segmented_sieve(n, segment_size=SEGMENT_SIZE):
    """
    Segmented Sieve of Eratosthenes to generate primes up to n.
    Yields primes in chunks to manage memory.

    Args:
        n (int): Upper bound for prime generation.
        segment_size (int): Size of each segment.

    Yields:
        list: A list of primes in the current segment.
    """
    if n < 2:
        return

    # Precompute primes up to sqrt(n) for sieving segments
    sqrt_n = int(math.sqrt(n)) + 1
    base_primes = simple_sieve(sqrt_n)
    logger.info(f"Base primes up to {sqrt_n}: {len(base_primes)} primes found.")

    # Initial segment
    low = 0
    high = min(segment_size, n)
    sieve = bytearray([1]) * (high - low)
    for p in base_primes:
        start = max(p*p, ((low + p - 1) // p) * p)
        if start < high:
            sieve[start - low : high - low : p] = bytearray([0]) * len(range(start - low, high - low, p))

    current_primes = [i + low for i, is_prime in enumerate(sieve) if is_prime and (i + low) >= 2]
    if current_primes:
        yield current_primes

    # Process subsequent segments
    low = high
    while low < n:
        high = min(low + segment_size, n)
        sieve = bytearray([1]) * (high - low)
        for p in base_primes:
            start = max(p*p, ((low + p - 1) // p) * p)
            if start < high:
                sieve[start - low : high - low : p] = bytearray([0]) * len(range(start - low, high - low, p))

        segment_primes = [i + low for i, is_prime in enumerate(sieve) if is_prime and (i + low) >= 2]
        if segment_primes:
            yield segment_primes
        low = high

def compute_normalized_gap(gap, p):
    """
    Compute normalized gap: gap / (log(p))^2.
    Used for distributional comparison (FR-003, FR-004).
    """
    if p <= 1:
        return 0.0
    log_p = math.log(p)
    return gap / (log_p ** 2)

def stream_gaps_to_csv(prime_generator, output_path):
    """
    Computes gaps between consecutive primes and streams them to a CSV file.
    This function handles the transition between segments to ensure all gaps are captured.

    Args:
        prime_generator: Generator yielding lists of primes.
        output_path (Path): Path to the output CSV file.
    """
    ensure_directories()
    logger.info(f"Starting gap computation. Output: {output_path}")

    prev_prime = None
    gap_count = 0
    start_time = time.time()

    # Open file in write mode with CSV writer
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # Write header as per spec Key Entities
        writer.writerow(['prime_before', 'prime_after', 'gap_size'])

        for segment in prime_generator:
            for p in segment:
                if prev_prime is not None:
                    gap = p - prev_prime
                    writer.writerow([prev_prime, p, gap])
                    gap_count += 1
                prev_prime = p

        # Log summary
        elapsed = time.time() - start_time
        logger.info(f"Gap computation complete. Processed {gap_count} gaps in {elapsed:.2f} seconds.")
        logger.info(f"Output written to: {output_path}")

    return gap_count

def run_pipeline(target_n=None, use_fallback=False):
    """
    Orchestrates the prime generation and gap computation pipeline.

    Args:
        target_n (int): The upper bound for prime generation.
        use_fallback (bool): If True, use FALLBACK_N if runtime is too long (simulated here by flag).

    Returns:
        dict: Pipeline execution summary.
    """
    if target_n is None:
        target_n = TARGET_N
    if use_fallback:
        target_n = FALLBACK_N
        logger.warning(f"Fallback mode activated. Using N={target_n} instead of {TARGET_N}.")

    logger.info(f"Initializing pipeline for N={target_n}")
    ensure_directories()

    # Determine output path based on target N
    if target_n == FALLBACK_N:
        output_path = PROJECT_ROOT / "data" / "raw" / "gaps_N10_9.csv"
        metadata_label = "fallback_N10_9"
    else:
        output_path = GAPS_OUTPUT_PATH
        metadata_label = "primary_N10_10"

    logger.info(f"Output path: {output_path} (Label: {metadata_label})")

    # Generate primes and compute gaps
    prime_gen = segmented_sieve(target_n)
    gap_count = stream_gaps_to_csv(prime_gen, output_path)

    # Update state checksums if state management is available
    try:
        state = load_state()
        update_state_checksums(state, [str(output_path)])
        save_state(state)
        logger.info("State checksums updated successfully.")
    except Exception as e:
        logger.warning(f"Could not update state checksums: {e}")

    return {
        "status": "success",
        "target_n": target_n,
        "output_file": str(output_path),
        "gap_count": gap_count,
        "label": metadata_label
    }

def main():
    """Entry point for the script."""
    logger.info("Starting Prime Gap Generation Pipeline (T012)")
    try:
        result = run_pipeline()
        logger.info(f"Pipeline completed successfully: {result}")
        return 0
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
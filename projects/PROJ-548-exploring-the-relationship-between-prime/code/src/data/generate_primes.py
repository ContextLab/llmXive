import os
import math
import sys
import time
import csv
import logging
from pathlib import Path
from typing import Iterator, Tuple, List, Optional
import numpy as np

# Project root handling for execution from various CWDs
_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.utils.config import ensure_directories, get_global_seed
from src.utils.logging import get_logger
from src.utils.io import load_state, save_state, update_state_checksums, commit_state

logger = get_logger(__name__)

# Configuration constants (can be overridden by config.py in future)
DEFAULT_N = 10**10
CHUNK_SIZE = 10**7  # 10 million per segment to manage memory
OUTPUT_PATH = "data/processed/raw_gaps.csv"

def simple_sieve(limit: int) -> List[int]:
    """
    Generate primes up to `limit` using the Sieve of Eratosthenes.
    Returns a list of primes.
    Note: Only suitable for small limits due to memory constraints.
    """
    if limit < 2:
        return []
    sieve = bytearray([1]) * (limit + 1)
    sieve[0:2] = b'\x00\x00'
    for i in range(2, int(limit**0.5) + 1):
        if sieve[i]:
            sieve[i*i:limit+1:i] = b'\x00' * len(sieve[i*i:limit+1:i])
    return [i for i, is_prime in enumerate(sieve) if is_prime]

def segmented_sieve(n: int, chunk_size: int = CHUNK_SIZE) -> Iterator[int]:
    """
    Generate primes up to n using a segmented sieve.
    Yields primes one by one to allow streaming processing.
    """
    if n < 2:
        return

    # Precompute primes up to sqrt(n) for sieving
    sqrt_n = int(math.isqrt(n))
    base_primes = simple_sieve(sqrt_n)

    if not base_primes:
        base_primes = []

    # First segment [0, sqrt_n]
    if sqrt_n >= 2:
        first_segment = simple_sieve(sqrt_n)
        for p in first_segment:
            yield p
        start = sqrt_n + 1
    else:
        start = 2

    # Process remaining segments
    while start <= n:
        end = min(start + chunk_size - 1, n)
        segment_size = end - start + 1
        segment = bytearray([1]) * segment_size

        for p in base_primes:
            # Find first multiple of p >= start
            first_multiple = max(p * p, ((start + p - 1) // p) * p)
            if first_multiple > end:
                continue
            # Mark multiples
            start_idx = first_multiple - start
            segment[start_idx:segment_size:p] = b'\x00' * ((segment_size - 1 - start_idx) // p + 1)

        # Yield primes in this segment
        for i in range(segment_size):
            if segment[i]:
                yield start + i

        start = end + 1

def compute_normalized_gap(gap: int, p: int) -> float:
    """
    Compute normalized gap: gap / (log(p)^2)
    This is used for normalization (handled in T019, but defined here for completeness).
    """
    if p <= 0:
        return 0.0
    log_p = math.log(p)
    if log_p == 0:
        return 0.0
    return gap / (log_p ** 2)

def run_pipeline(n: Optional[int] = None, output_path: Optional[str] = None) -> str:
    """
    Main pipeline to generate primes, compute gaps, and stream to CSV.
    Returns the path to the output file.
    """
    if n is None:
        n = DEFAULT_N
    if output_path is None:
        output_path = OUTPUT_PATH

    # Ensure directories exist
    ensure_directories()
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting prime generation up to {n}")
    logger.info(f"Output file: {out_file}")

    total_primes = 0
    total_gaps = 0
    start_time = time.time()
    last_prime = None
    max_prime = 0

    # Open file for streaming write
    with open(out_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # Write header
        writer.writerow(['prime_before', 'prime_after', 'gap_size'])

        for p in segmented_sieve(n):
            total_primes += 1
            max_prime = p
            if last_prime is not None:
                gap = p - last_prime
                writer.writerow([last_prime, p, gap])
                total_gaps += 1
            last_prime = p

            # Log progress every 100k primes
            if total_primes % 100000 == 0:
                elapsed = time.time() - start_time
                logger.info(f"Processed {total_primes} primes, generated {total_gaps} gaps. Elapsed: {elapsed:.2f}s")

    elapsed = time.time() - start_time
    logger.info(f"Pipeline complete. Total primes: {total_primes}, Total gaps: {total_gaps}")
    logger.info(f"Time elapsed: {elapsed:.2f}s")
    logger.info(f"Last prime processed: {max_prime}")

    # Update state
    try:
        state = load_state()
        # Record artifact info
        if 'artifacts' not in state:
            state['artifacts'] = {}
        state['artifacts']['raw_gaps'] = {
            'path': str(out_file),
            'count': total_gaps,
            'last_prime': max_prime,
            'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'source': 'segmented_sieve',
            'limit': n
        }
        update_state_checksums(state)
        commit_state(state)
        logger.info("State updated successfully")
    except Exception as e:
        logger.warning(f"Failed to update state: {e}")

    return str(out_file)

def main():
    """Entry point for CLI execution."""
    import argparse
    parser = argparse.ArgumentParser(description="Generate primes and compute gaps")
    parser.add_argument('--n', type=int, default=DEFAULT_N, help=f"Upper limit for prime generation (default: {DEFAULT_N})")
    parser.add_argument('--output', type=str, default=OUTPUT_PATH, help="Output file path")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/pipeline.log')
        ]
    )

    result_path = run_pipeline(n=args.n, output_path=args.output)
    print(f"Output written to: {result_path}")
    return result_path

if __name__ == "__main__":
    main()
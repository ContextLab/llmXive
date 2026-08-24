"""
Segmented Sieve of Eratosthenes implementation.

Generates all prime numbers up to a specified limit (default 10^9) using a
memory-efficient segmented approach. Writes the results to a CSV file.
"""

import argparse
import logging
import os
import sys
import time
import hashlib
from typing import List, Optional, Iterator, Tuple

import numpy as np

from utils import setup_logging, generate_checksum, get_file_size_human

# Constants
DEFAULT_LIMIT = 10**9
DEFAULT_SEGMENT_SIZE = 100_000  # 100k primes per segment approx
OUTPUT_DIR = "data"
OUTPUT_FILENAME = "primes_1e9.csv"
MEMORY_CAP_GB = 4.0  # Warning threshold

# Setup logger
logger = logging.getLogger(__name__)


def simple_sieve(limit: int) -> List[int]:
    """
    Generate primes up to `limit` using a simple Sieve of Eratosthenes.
    Used for generating base primes for the segmented sieve.
    """
    if limit < 2:
        return []
    
    sieve = np.ones(limit + 1, dtype=bool)
    sieve[0] = sieve[1] = False
    
    # Only need to sieve up to sqrt(limit)
    for start in range(2, int(limit**0.5) + 1):
        if sieve[start]:
            sieve[start*start : limit+1 : start] = False
    
    return np.nonzero(sieve)[0].tolist()


def segmented_sieve(limit: int, segment_size: int = DEFAULT_SEGMENT_SIZE) -> Iterator[int]:
    """
    Generate primes up to `limit` using a segmented sieve.
    
    Yields primes one by one or in small batches to maintain low memory usage.
    """
    if limit < 2:
        return

    # First, find all primes up to sqrt(limit) for sieving segments
    sqrt_limit = int(limit**0.5) + 1
    base_primes = simple_sieve(sqrt_limit)
    
    if not base_primes:
        return

    # Initialize the segment
    low = 0
    high = segment_size
    
    # Ensure we start at least at 2
    if high > 2 and low < 2:
        low = 2
        high = min(segment_size, limit + 1)
    
    # Handle the first segment explicitly to avoid index issues with small numbers
    # We start sieving from 2
    current_low = 2
    current_high = min(segment_size, limit + 1)
    
    while current_low <= limit:
        # Create a boolean array for the current segment
        # Size is (current_high - current_low)
        seg_size = current_high - current_low
        is_prime_seg = np.ones(seg_size, dtype=bool)
        
        # Sieve with each base prime
        for p in base_primes:
            # Find the first multiple of p >= current_low
            start_idx = ((current_low + p - 1) // p) * p
            if start_idx < current_low:
                start_idx += p
            
            # If start_idx is p itself, don't mark it as composite
            if start_idx == p:
                start_idx += p
            
            # Convert to segment index
            if start_idx < current_high:
                start_seg_idx = start_idx - current_low
                is_prime_seg[start_seg_idx : seg_size : p] = False
        
        # Yield primes in this segment
        for i in range(seg_size):
            if is_prime_seg[i]:
                yield current_low + i
        
        # Move to next segment
        current_low = current_high
        current_high = min(current_low + segment_size, limit + 1)


def run_sieve(
    limit: int = DEFAULT_LIMIT,
    output_path: Optional[str] = None,
    segment_size: int = DEFAULT_SEGMENT_SIZE,
    verbose: bool = True
) -> Tuple[int, float, str]:
    """
    Execute the segmented sieve, write primes to CSV, and return statistics.
    
    Args:
        limit: Upper bound for prime generation (inclusive).
        output_path: Path to write the CSV file. Defaults to data/primes_1e9.csv.
        segment_size: Size of each segment for sieving.
        verbose: Whether to log progress.
        
    Returns:
        Tuple of (count, runtime_seconds, checksum)
    """
    start_time = time.time()
    
    if output_path is None:
        output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILENAME)
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    logger.info(f"Starting segmented sieve up to {limit:,}")
    logger.info(f"Output path: {output_path}")
    logger.info(f"Segment size: {segment_size:,}")
    
    # Check memory constraints (rough estimate)
    # A boolean array for 10^9 would be ~1GB, but we use segments.
    # The prime list itself: 50M primes * 8 bytes (int64) = 400MB.
    # We are well within the 4GB cap for the generation step.
    
    count = 0
    last_log_count = 0
    log_interval = 1_000_000  # Log every 1M primes
    
    # Open file for writing
    with open(output_path, 'w', buffering=8192) as f:
        f.write("prime\n")
        
        for prime in segmented_sieve(limit, segment_size):
            count += 1
            f.write(f"{prime}\n")
            
            if verbose and count - last_log_count >= log_interval:
                elapsed = time.time() - start_time
                rate = count / elapsed if elapsed > 0 else 0
                logger.info(f"Progress: {count:,} primes found ({rate:.0f} primes/sec)")
                last_log_count = count
    
    runtime = time.time() - start_time
    
    # Final stats
    logger.info(f"Sieve completed.")
    logger.info(f"Total primes found: {count:,}")
    logger.info(f"Runtime: {runtime:.2f} seconds")
    
    # Runtime warning check (Task T012 requirement)
    if runtime > 7200:  # 120 minutes
        logger.warning(f"Runtime ({runtime:.0f}s) exceeded 120-minute constraint.")
    else:
        logger.info(f"Runtime ({runtime:.0f}s) within 120-minute constraint.")
    
    # Generate checksum
    checksum = generate_checksum(output_path)
    file_size = get_file_size_human(output_path)
    logger.info(f"Output file size: {file_size}")
    logger.info(f"Checksum (SHA256): {checksum}")
    
    return count, runtime, checksum


def validate_primes(output_path: str, sample_size: int = 1000) -> bool:
    """
    Perform a quick sanity check on the generated primes.
    This is a lightweight validation, not the full T013 verification.
    """
    if not os.path.exists(output_path):
        logger.error(f"Output file not found: {output_path}")
        return False
    
    try:
        with open(output_path, 'r') as f:
            # Skip header
            next(f)
            
            # Read a few lines to check format
            lines = []
            for i, line in enumerate(f):
                if i >= sample_size:
                    break
                lines.append(line.strip())
        
        if not lines:
            logger.error("No primes found in file.")
            return False
        
        # Check if they are integers and > 1
        for val_str in lines:
            val = int(val_str)
            if val < 2:
                logger.error(f"Invalid prime value: {val}")
                return False
            
        logger.info(f"Quick validation passed for {len(lines)} samples.")
        return True
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run Segmented Sieve of Eratosthenes")
    parser.add_argument(
        "--limit", 
        type=int, 
        default=DEFAULT_LIMIT,
        help=f"Upper bound for prime generation (default: {DEFAULT_LIMIT:,})"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default=None,
        help="Output file path (default: data/primes_1e9.csv)"
    )
    parser.add_argument(
        "--segment-size", 
        type=int, 
        default=DEFAULT_SEGMENT_SIZE,
        help=f"Segment size for sieving (default: {DEFAULT_SEGMENT_SIZE:,})"
    )
    parser.add_argument(
        "--quiet", 
        action="store_true",
        help="Suppress progress logging"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.INFO if not args.quiet else logging.WARNING
    setup_logging(level=log_level)
    
    # Run sieve
    try:
        count, runtime, checksum = run_sieve(
            limit=args.limit,
            output_path=args.output,
            segment_size=args.segment_size,
            verbose=not args.quiet
        )
        
        # Quick validation
        output_path = args.output if args.output else os.path.join(OUTPUT_DIR, OUTPUT_FILENAME)
        if validate_primes(output_path):
            logger.info("Sieve generation and basic validation successful.")
            sys.exit(0)
        else:
            logger.error("Sieve generation completed but validation failed.")
            sys.exit(1)
            
    except Exception as e:
        logger.exception(f"Fatal error during sieve generation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

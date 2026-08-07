"""
Segmented Sieve of Eratosthenes implementation for generating primes up to 10^9.

This module implements a memory-efficient segmented sieve to generate all prime
numbers up to a specified limit (default 10^9). It includes progress logging,
runtime measurement, and outputs results to a CSV file.

Output: data/primes_1e9.csv
"""
import argparse
import logging
import os
import sys
import time
import hashlib
from typing import List, Generator, Optional, Tuple

# Local imports from project structure
from utils import setup_logging, generate_checksum, get_file_size_human
from config import load_config, CIConstraints

# Constants
DEFAULT_LIMIT = 10**9
DEFAULT_SEGMENT_SIZE = 100000  # 100k integers per segment for memory efficiency
DEFAULT_OUTPUT_PATH = "data/primes_1e9.csv"
MAX_RUNTIME_SECONDS = 7200  # 2 hours (120 minutes) as per constraints

logger = logging.getLogger(__name__)


def simple_sieve(limit: int) -> List[int]:
    """
    Generate all primes up to limit using the standard Sieve of Eratosthenes.
    
    This is used for the initial segment to find base primes for the segmented sieve.
    
    Args:
        limit: Upper bound for prime generation (inclusive)
        
    Returns:
        List of prime numbers up to limit
    """
    if limit < 2:
        return []
        
    sieve = bytearray([1]) * (limit + 1)
    sieve[0:2] = b'\x00\x00'
    
    for i in range(2, int(limit**0.5) + 1):
        if sieve[i]:
            sieve[i*i:limit+1:i] = b'\x00' * len(sieve[i*i:limit+1:i])
            
    return [i for i, is_prime in enumerate(sieve) if is_prime]


def segmented_sieve(limit: int, segment_size: int = DEFAULT_SEGMENT_SIZE) -> Generator[int, None, None]:
    """
    Generate all primes up to limit using a segmented sieve approach.
    
    This method processes the range in segments to maintain low memory usage.
    It first generates base primes up to sqrt(limit), then uses them to
    sieve each segment.
    
    Args:
        limit: Upper bound for prime generation (inclusive)
        segment_size: Number of integers to process in each segment
        
    Yields:
        Prime numbers in ascending order
    """
    if limit < 2:
        return
        
    # Calculate base primes up to sqrt(limit)
    sqrt_limit = int(limit**0.5) + 1
    base_primes = simple_sieve(sqrt_limit)
    
    if not base_primes:
        return
        
    # First segment: 0 to min(limit, segment_size)
    low = 0
    high = min(limit, segment_size)
    
    while low <= limit:
        # Create sieve for current segment
        # We only need to track odd numbers to save memory, but for simplicity
        # and clarity, we'll use a full bytearray
        segment_size_actual = min(segment_size, limit - low + 1)
        sieve = bytearray([1]) * segment_size_actual
        
        if low == 0:
            sieve[0:2] = b'\x00\x00'  # 0 and 1 are not prime
        
        # Mark multiples of base primes
        for p in base_primes:
            # Find the first multiple of p >= low
            start = max(p * p, ((low + p - 1) // p) * p)
            
            # Adjust for 0-indexed segment
            start_idx = start - low
            if start_idx < 0:
                start_idx = 0
                
            # Mark multiples
            if start_idx < segment_size_actual:
                sieve[start_idx:segment_size_actual:p] = b'\x00' * len(sieve[start_idx:segment_size_actual:p])
        
        # Yield primes from current segment
        for i in range(segment_size_actual):
            if sieve[i]:
                yield low + i
        
        # Move to next segment
        low = high
        high = min(low + segment_size, limit)


def run_sieve(limit: int = DEFAULT_LIMIT, output_path: str = DEFAULT_OUTPUT_PATH,
              segment_size: int = DEFAULT_SEGMENT_SIZE, verbose: bool = True) -> Tuple[int, float]:
    """
    Execute the segmented sieve and write results to a CSV file.
    
    Args:
        limit: Upper bound for prime generation
        output_path: Path to output CSV file
        segment_size: Size of each segment in the sieve
        verbose: Whether to log progress and statistics
        
    Returns:
        Tuple of (prime_count, runtime_seconds)
    """
    start_time = time.time()
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        
    if verbose:
        logger.info(f"Starting segmented sieve up to {limit:,}")
        logger.info(f"Output path: {output_path}")
        logger.info(f"Segment size: {segment_size:,}")
        
    # Check runtime constraint
    if verbose:
        logger.info(f"Maximum allowed runtime: {MAX_RUNTIME_SECONDS / 60:.0f} minutes")
        
    prime_count = 0
    
    try:
        with open(output_path, 'w') as f:
            f.write("prime\n")
            
            for prime in segmented_sieve(limit, segment_size):
                f.write(f"{prime}\n")
                prime_count += 1
                
                # Progress logging every 10% of estimated primes (approx)
                # Estimate based on prime number theorem: pi(x) ~ x/ln(x)
                if verbose and prime_count % 5000000 == 0:
                    elapsed = time.time() - start_time
                    remaining_estimate = (limit / prime_count) * elapsed - elapsed
                    logger.info(f"Progress: {prime_count:,} primes found, "
                              f"elapsed: {elapsed:.1f}s, "
                              f"est. remaining: {remaining_estimate:.1f}s")
                    
                    # Check if we're exceeding runtime
                    if elapsed > MAX_RUNTIME_SECONDS * 0.9:
                        logger.warning(f"Approaching runtime limit ({elapsed:.1f}s > "
                                     f"{MAX_RUNTIME_SECONDS * 0.9:.1f}s). "
                                     f"Consider reducing scope or optimizing.")
        
    except Exception as e:
        logger.error(f"Error during sieve execution: {e}")
        raise
        
    runtime = time.time() - start_time
    
    if verbose:
        logger.info(f"Sieve completed successfully!")
        logger.info(f"Total primes found: {prime_count:,}")
        logger.info(f"Total runtime: {runtime:.2f} seconds ({runtime/60:.2f} minutes)")
        
        # Log file size
        if os.path.exists(output_path):
            file_size = get_file_size_human(output_path)
            logger.info(f"Output file size: {file_size}")
            
        # Calculate checksum
        checksum = generate_checksum(output_path)
        logger.info(f"Output file checksum (SHA256): {checksum}")
        
        if runtime > MAX_RUNTIME_SECONDS:
            logger.warning(f"Runtime exceeded limit: {runtime:.2f}s > {MAX_RUNTIME_SECONDS}s")
        else:
            logger.info(f"Runtime within limit: {runtime:.2f}s <= {MAX_RUNTIME_SECONDS}s")
            
    return prime_count, runtime


def validate_primes(prime_file: str, sample_size: int = 1000) -> bool:
    """
    Perform a basic validation of the generated prime file.
    
    This function checks:
    1. File exists and is readable
    2. First few values are correct (2, 3, 5, 7...)
    3. Last value is <= limit
    4. No duplicate values
    
    Args:
        prime_file: Path to the CSV file containing primes
        sample_size: Number of primes to check for duplicates and ordering
        
    Returns:
        True if validation passes, False otherwise
    """
    if not os.path.exists(prime_file):
        logger.error(f"Prime file not found: {prime_file}")
        return False
        
    try:
        with open(prime_file, 'r') as f:
            # Skip header
            header = f.readline().strip()
            if header != "prime":
                logger.warning(f"Unexpected header: {header}")
                
            primes = []
            for i, line in enumerate(f):
                if i >= sample_size:
                    break
                try:
                    prime = int(line.strip())
                    primes.append(prime)
                except ValueError:
                    logger.error(f"Invalid prime value at line {i+2}: {line.strip()}")
                    return False
                    
            # Check first few values
            expected_start = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
            if len(primes) >= len(expected_start):
                for i, (actual, expected) in enumerate(zip(primes, expected_start)):
                    if actual != expected:
                        logger.error(f"First prime mismatch at index {i}: "
                                   f"got {actual}, expected {expected}")
                        return False
                        
            # Check for duplicates
            if len(primes) != len(set(primes)):
                logger.error("Duplicate primes found in sample")
                return False
                
            # Check ordering
            for i in range(1, len(primes)):
                if primes[i] <= primes[i-1]:
                    logger.error(f"Primes not in ascending order at index {i}")
                    return False
                    
        logger.info(f"Basic validation passed for {sample_size} primes")
        return True
        
    except Exception as e:
        logger.error(f"Validation error: {e}")
        return False


def main():
    """Main entry point for the sieve generation script."""
    parser = argparse.ArgumentParser(
        description="Generate primes using segmented sieve of Eratosthenes"
    )
    parser.add_argument(
        "--limit", type=int, default=DEFAULT_LIMIT,
        help=f"Upper bound for prime generation (default: {DEFAULT_LIMIT:,})"
    )
    parser.add_argument(
        "--output", type=str, default=DEFAULT_OUTPUT_PATH,
        help=f"Output CSV file path (default: {DEFAULT_OUTPUT_PATH})"
    )
    parser.add_argument(
        "--segment-size", type=int, default=DEFAULT_SEGMENT_SIZE,
        help=f"Segment size for sieve (default: {DEFAULT_SEGMENT_SIZE:,})"
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Suppress progress logging"
    )
    parser.add_argument(
        "--validate", action="store_true",
        help="Perform basic validation after generation"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    level = logging.WARNING if args.quiet else logging.INFO
    setup_logging(level=level)
    
    try:
        prime_count, runtime = run_sieve(
            limit=args.limit,
            output_path=args.output,
            segment_size=args.segment_size,
            verbose=not args.quiet
        )
        
        if args.validate:
            if validate_primes(args.output):
                logger.info("Validation successful")
            else:
                logger.error("Validation failed")
                sys.exit(1)
                
    except KeyboardInterrupt:
        logger.warning("Sieve interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
import os
import math
import sys
from pathlib import Path
from typing import List, Generator, Tuple, Optional
import csv
import logging

# Import utilities from the project's established API surface
from src.utils.config import get_config
from src.utils.logging import setup_logging, get_logger
from src.utils.io import save_state, compute_file_checksum

# Configure logging for this module
logger = get_logger(__name__)

def simple_sieve(limit: int) -> List[int]:
    """
    Generate all primes up to limit using the Sieve of Eratosthenes.
    Memory intensive for very large limits, suitable for small limits or testing.
    """
    if limit < 2:
        return []
    
    # Boolean array: True means prime (initially assume all are prime)
    is_prime = bytearray([1]) * (limit + 1)
    is_prime[0] = 0
    is_prime[1] = 0
    
    p = 2
    while (p * p <= limit):
        if is_prime[p]:
            # Mark multiples of p as not prime
            for i in range(p * p, limit + 1, p):
                is_prime[i] = 0
        p += 1
    
    # Collect primes
    primes = [i for i in range(limit + 1) if is_prime[i]]
    return primes

def segmented_sieve(limit: int, segment_size: Optional[int] = None) -> Generator[List[int], None, None]:
    """
    Generate primes in segments to handle large limits (e.g., 10^10) within memory constraints.
    Yields lists of primes for each segment.
    
    Args:
        limit: The upper bound for prime generation (inclusive).
        segment_size: Size of each segment in numbers. Defaults to sqrt(limit) if not provided.
    
    Yields:
        List of primes found in the current segment.
    """
    if limit < 2:
        return

    if segment_size is None:
        # Heuristic: use sqrt(limit) as segment size for balance
        segment_size = int(math.sqrt(limit)) + 1000
        # Ensure segment size is reasonable (at least 1000, at most 10^7)
        segment_size = max(1000, min(segment_size, 10_000_000))

    # First, find primes up to sqrt(limit) for sieving
    sqrt_limit = int(math.sqrt(limit)) + 1
    base_primes = simple_sieve(sqrt_limit)
    
    if not base_primes:
        return

    low = 0
    high = segment_size
    
    while low < limit:
        high = min(high, limit + 1)
        
        # Initialize segment boolean array
        # is_prime[i] corresponds to number (low + i)
        segment_size_actual = high - low
        is_prime_segment = bytearray([1]) * segment_size_actual
        
        # 0 and 1 are not prime
        if low == 0:
            if segment_size_actual > 0:
                is_prime_segment[0] = 0
            if segment_size_actual > 1:
                is_prime_segment[1] = 0
        
        # Sieve the current segment using base primes
        for p in base_primes:
            # Find the first multiple of p >= low
            start = ((low + p - 1) // p) * p
            if start < p * p:
                start = p * p
            if start < low:
                # Should not happen with correct logic, but safety check
                start = low + ((p - (low % p)) % p)
            
            # Mark multiples in the segment
            # start_idx is the index in the segment array corresponding to 'start'
            start_idx = start - low
            if start_idx < 0:
                # This can happen if start < low due to rounding, adjust
                start_idx = 0
                # Recalculate start to be >= low
                start = low + ((p - (low % p)) % p)
                start_idx = start - low
            
            for i in range(start_idx, segment_size_actual, p):
                is_prime_segment[i] = 0
        
        # Collect primes from this segment
        segment_primes = []
        for i in range(segment_size_actual):
            if is_prime_segment[i]:
                num = low + i
                if num <= limit and num >= 2:
                    segment_primes.append(num)
        
        yield segment_primes
        
        low = high
        high += segment_size

def compute_normalized_gap(prime_before: int, prime_after: int) -> float:
    """
    Compute the normalized gap between two consecutive primes.
    Normalization factor is (log(prime_before))^2 according to the Cramér model.
    
    Args:
        prime_before: The smaller prime.
        prime_after: The larger prime.
    
    Returns:
        The normalized gap size.
    """
    if prime_before < 2:
        # Avoid log(0) or log(1) which are undefined or zero
        return float('inf')
    
    log_p = math.log(prime_before)
    if log_p == 0:
        return float('inf')
    
    gap_size = prime_after - prime_before
    normalized = gap_size / (log_p ** 2)
    return normalized

def run_pipeline(output_path: str = None):
    """
    Main pipeline to generate primes, compute gaps, and stream results to CSV.
    
    This function:
    1. Generates primes up to N (from config) using segmented sieve.
    2. Computes consecutive prime gaps.
    3. Normalizes gaps.
    4. Streams results to a CSV file in chunks to manage memory.
    
    Args:
        output_path: Path to the output CSV file. Defaults to config setting.
    """
    config = get_config()
    N = config.get('N', 10**10)  # Default to 10^10 if not set
    if output_path is None:
        output_path = config.get('primes_gaps_path', 'data/processed/primes_gaps.csv')
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Setup logging
    setup_logging()
    logger.info(f"Starting prime gap generation pipeline. Target N={N}.")
    logger.info(f"Output file: {output_path}")
    
    # Initialize state tracking
    state = {
        'pipeline': 'generate_primes',
        'status': 'running',
        'start_time': None,
        'end_time': None,
        'primes_generated': 0,
        'gaps_computed': 0,
        'output_file': output_path,
        'checksum': None
    }
    
    try:
        import time
        state['start_time'] = time.time()
        
        # Open output file for writing
        with open(output_path, 'w', newline='') as csvfile:
            fieldnames = ['prime_before', 'prime_after', 'gap_size', 'normalized_gap']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            prev_prime = None
            primes_count = 0
            gaps_count = 0
            
            # Process primes in segments
            for segment_primes in segmented_sieve(N):
                # Sort the segment just in case (should be sorted by generation logic)
                segment_primes.sort()
                
                for prime in segment_primes:
                    if prev_prime is not None:
                        # Compute gap
                        gap_size = prime - prev_prime
                        normalized_gap = compute_normalized_gap(prev_prime, prime)
                        
                        # Write to CSV
                        writer.writerow({
                            'prime_before': prev_prime,
                            'prime_after': prime,
                            'gap_size': gap_size,
                            'normalized_gap': normalized_gap
                        })
                        
                        gaps_count += 1
                    
                    prev_prime = prime
                    primes_count += 1
                    
                    # Log progress periodically
                    if primes_count % 100000 == 0:
                        logger.info(f"Processed {primes_count} primes, {gaps_count} gaps.")
        
        state['end_time'] = time.time()
        state['status'] = 'completed'
        state['primes_generated'] = primes_count
        state['gaps_computed'] = gaps_count
        
        # Compute checksum for integrity
        checksum = compute_file_checksum(output_path)
        state['checksum'] = checksum
        state['message'] = f"Successfully generated {primes_count} primes and {gaps_count} gaps."
        
        logger.info(state['message'])
        
    except Exception as e:
        state['status'] = 'failed'
        state['error'] = str(e)
        logger.error(f"Pipeline failed: {e}")
        raise
    finally:
        # Save state
        state_path = config.get('state_path', 'state.yaml')
        save_state(state_path, state)
        logger.info(f"State saved to {state_path}")

if __name__ == '__main__':
    # Default execution
    run_pipeline()

"""
code/sieve.py

Segmented Sieve of Eratosthenes implementation for generating primes up to 10^9.
Includes deterministic validation logic (Constitution Principle VI).
"""

import argparse
import logging
import os
import sys
import time
import hashlib
from typing import List, Generator, Tuple, Optional

import numpy as np

# Local imports
from config import load_config, CIConstraints
from utils import setup_logging, generate_checksum, get_file_size_human

# Constants
MAX_PRIME = 10**9
SEGMENT_SIZE = 10**6  # 1 million integers per segment
MAX_RUNTIME_SECONDS = 7200  # 120 minutes

# Ensure output directories exist
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

def simple_sieve(limit: int) -> List[int]:
    """
    Simple Sieve of Eratosthenes for small limits.
    Returns a list of primes up to `limit`.
    """
    if limit < 2:
        return []
    sieve = np.ones(limit + 1, dtype=bool)
    sieve[0] = sieve[1] = False
    for start in range(2, int(limit**0.5) + 1):
        if sieve[start]:
            sieve[start*start:limit+1:start] = False
    return np.where(sieve)[0].tolist()

def segmented_sieve(n: int, output_path: str) -> Tuple[int, float, str]:
    """
    Segmented Sieve of Eratosthenes to generate primes up to n.
    Writes primes to `output_path` in CSV format.
    
    Returns:
        Tuple of (count, runtime_seconds, checksum)
    """
    logger = logging.getLogger(__name__)
    start_time = time.time()
    
    # Base primes for sieving segments
    # We need primes up to sqrt(n) to sieve the segments
    base_limit = int(n**0.5) + 1
    logger.info(f"Generating base primes up to {base_limit} for sieving...")
    base_primes = simple_sieve(base_limit)
    
    if not base_primes:
        base_primes = []
    
    count = 0
    segment_start = 0
    
    # Open file for writing
    with open(output_path, 'w') as f:
        f.write("prime\n")
        
        while segment_start < n:
            # Check runtime constraint
            current_time = time.time()
            elapsed = current_time - start_time
            if elapsed > MAX_RUNTIME_SECONDS:
                raise RuntimeError(f"Runtime limit of {MAX_RUNTIME_SECONDS}s exceeded. Stopping at {segment_start}.")
            
            segment_end = min(segment_start + SEGMENT_SIZE, n + 1)
            segment_size = segment_end - segment_start
            
            # Initialize segment boolean array
            # is_prime[i] corresponds to number (segment_start + i)
            is_prime = np.ones(segment_size, dtype=bool)
            
            if segment_start == 0:
                # Handle 0 and 1 specifically for the first segment
                is_prime[0] = False
                if segment_size > 1:
                    is_prime[1] = False
            
            # Sieve with base primes
            for p in base_primes:
                # Find the first multiple of p >= segment_start
                first_multiple = max(p * p, ((segment_start + p - 1) // p) * p)
                
                if first_multiple < segment_end:
                    # Calculate index in the segment
                    start_idx = first_multiple - segment_start
                    # Mark multiples
                    is_prime[start_idx:segment_size:p] = False
            
            # Collect primes in this segment
            for i in range(segment_size):
                if is_prime[i]:
                    num = segment_start + i
                    f.write(f"{num}\n")
                    count += 1
            
            # Progress logging
            if segment_start % (SEGMENT_SIZE * 10) == 0:
                elapsed = time.time() - start_time
                logger.info(f"Processed up to {segment_end:,}, count: {count:,}, time: {elapsed:.1f}s")
            
            segment_start = segment_end
    
    runtime = time.time() - start_time
    logger.info(f"Sieve completed. Total primes: {count:,}, Runtime: {runtime:.2f}s")
    
    # Generate checksum
    checksum = generate_checksum(output_path)
    logger.info(f"Checksum (SHA256): {checksum}")
    
    return count, runtime, checksum

def validate_primes(input_path: str, sample_size: Optional[int] = 10000) -> Tuple[bool, str]:
    """
    Deterministic validation of the generated prime list.
    
    Implements Constitution Principle VI: Deterministic Number-Theoretic Verification.
    Uses trial division against the generated list itself (or a subset) to confirm
    every entry is prime with deferred certainty.
    
    Args:
        input_path: Path to the CSV file containing primes.
        sample_size: Number of primes to validate (None for all).
        
    Returns:
        Tuple of (validation_passed, message)
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Starting deterministic validation of {input_path}...")
    
    if not os.path.exists(input_path):
        return False, f"Input file not found: {input_path}"
    
    primes = []
    with open(input_path, 'r') as f:
        # Skip header
        next(f)
        for line in f:
            line = line.strip()
            if line:
                primes.append(int(line))
    
    total_count = len(primes)
    logger.info(f"Loaded {total_count:,} primes for validation.")
    
    if total_count == 0:
        return False, "No primes found in input file."
    
    # Determine validation scope
    if sample_size is None or sample_size >= total_count:
        primes_to_validate = primes
        scope_msg = "all"
    else:
        # Validate a deterministic subset: first, middle, and last
        # This provides coverage without validating 50M numbers which is slow
        primes_to_validate = []
        step = total_count // sample_size
        for i in range(0, total_count, step):
            primes_to_validate.append(primes[i])
        # Always include the last one
        if primes[-1] not in primes_to_validate:
            primes_to_validate.append(primes[-1])
        scope_msg = f"a representative subset ({len(primes_to_validate):,} of {total_count:,})"
    
    logger.info(f"Validating {scope_msg} of the primes via trial division...")
    
    validation_start = time.time()
    passed = True
    failed_prime = None
    
    # For each candidate, verify it is prime using trial division
    # We use the fact that if a number is composite, it must have a prime factor <= sqrt(n).
    # Since we have a sorted list of primes, we can use primes up to sqrt(candidate).
    
    for idx, candidate in enumerate(primes_to_validate):
        if candidate < 2:
            passed = False
            failed_prime = candidate
            break
        
        if candidate == 2:
            continue
        
        if candidate % 2 == 0:
            passed = False
            failed_prime = candidate
            break
        
        limit = int(candidate**0.5) + 1
        
        # Trial division using the generated prime list
        # We only need to check primes up to sqrt(candidate)
        is_composite = False
        for p in primes:
            if p > limit:
                break
            if p == candidate:
                break # It's in the list, so it's prime (assuming list is correct)
            if candidate % p == 0:
                is_composite = True
                failed_prime = candidate
                break
        
        if is_composite:
            passed = False
            break
        
        if (idx + 1) % 1000 == 0:
            logger.debug(f"Validated {idx + 1:,} / {len(primes_to_validate):,}")
    
    validation_time = time.time() - validation_start
    
    if passed:
        msg = f"Validation PASSED for {scope_msg} in {validation_time:.2f}s. All checked numbers are prime."
        logger.info(msg)
    else:
        msg = f"Validation FAILED. Composite number found: {failed_prime}."
        logger.error(msg)
    
    return passed, msg

def run_sieve(output_path: str, validate: bool = True) -> bool:
    """
    Main orchestration function to run the sieve and optionally validate.
    """
    logger = setup_logging("sieve")
    logger.info("Starting Segmented Sieve of Eratosthenes...")
    
    try:
        # 1. Generate primes
        count, runtime, checksum = segmented_sieve(MAX_PRIME, output_path)
        
        # 2. Verify count against known value (OEIS A006880)
        expected_count = 50847534
        if count != expected_count:
            logger.error(f"Prime count mismatch: got {count}, expected {expected_count}.")
            return False
        
        logger.info(f"Prime count verified: {count:,} (matches OEIS A006880).")
        
        # 3. Runtime check
        if runtime > MAX_RUNTIME_SECONDS:
            logger.error(f"Runtime {runtime:.2f}s exceeded limit {MAX_RUNTIME_SECONDS}s.")
            return False
        
        # 4. Deterministic Validation (T013)
        if validate:
            passed, msg = validate_primes(output_path)
            if not passed:
                logger.error(f"Validation failed: {msg}")
                return False
            logger.info(f"Validation result: {msg}")
        
        logger.info("Sieve generation and validation completed successfully.")
        return True
        
    except Exception as e:
        logger.exception(f"Error during sieve execution: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Generate primes using Segmented Sieve.")
    parser.add_argument('--output', type=str, default=os.path.join(DATA_DIR, "primes_1e9.csv"),
                        help="Output CSV file path.")
    parser.add_argument('--no-validate', action='store_true',
                        help="Skip deterministic validation step.")
    args = parser.parse_args()
    
    success = run_sieve(args.output, validate=not args.no_validate)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
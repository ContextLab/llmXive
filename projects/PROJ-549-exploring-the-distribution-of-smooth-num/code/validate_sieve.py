"""
validate_sieve.py

Verifies the generated prime list from data/primes_1e9.csv.

Requirements:
1. DO NOT use a secondary deterministic sieve or probabilistic tests.
2. Verify total count exactly equals 50,847,534 (OEIS A006880).
3. Randomly sample a set of primes from the list and verify each using 
   deterministic trial division against the generated prime list itself 
   (up to sqrt(p)) to ensure primality.
4. Output a checksum and a boolean flag validation_passed.
"""
import argparse
import csv
import hashlib
import json
import logging
import math
import os
import random
import sys
import time
from typing import List, Optional, Set, Tuple, Dict, Any

from utils import setup_logging, generate_checksum

# Constants
EXPECTED_PRIME_COUNT = 50847534  # OEIS A006880 for pi(10^9)
INPUT_FILE = "data/primes_1e9.csv"
OUTPUT_FILE = "data/validation_report.json"
SAMPLE_SIZE = 1000  # Number of primes to sample for verification
MAX_PRIME = 1_000_000_000

logger = logging.getLogger(__name__)

def load_primes_from_csv(filepath: str) -> List[int]:
    """Load primes from a CSV file (one prime per line)."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Input file not found: {filepath}")
    
    primes = []
    with open(filepath, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if row:
                try:
                    primes.append(int(row[0]))
                except ValueError:
                    logger.warning(f"Skipping non-integer value: {row[0]}")
    return primes

def is_prime_trial_division(n: int, primes_list: List[int]) -> bool:
    """
    Verify primality of n using deterministic trial division against 
    the provided prime list up to sqrt(n).
    
    This satisfies Constitution Principle VI by using a deterministic method
    rather than probabilistic tests.
    """
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    
    limit = int(math.isqrt(n)) + 1
    
    # Use the provided prime list for trial division
    for p in primes_list:
        if p > limit:
            break
        if n % p == 0:
            return False
    
    return True

def verify_primes_sample(primes: List[int], sample_size: int) -> Tuple[bool, List[int], List[bool]]:
    """
    Randomly sample primes and verify each using trial division.
    
    Returns:
      Tuple of (all_passed, sampled_indices, verification_results)
    """
    if len(primes) < sample_size:
        logger.warning(f"Prime list has {len(primes)} items, less than sample size {sample_size}")
        sample_size = len(primes)
    
    # Randomly select indices
    indices = random.sample(range(len(primes)), sample_size)
    results = []
    all_passed = True
    
    for idx in indices:
        prime_val = primes[idx]
        # Verify primality using trial division against the prime list itself
        is_prime = is_prime_trial_division(prime_val, primes)
        results.append(is_prime)
        if not is_prime:
            all_passed = False
            logger.error(f"Prime at index {idx} (value {prime_val}) failed verification")
    
    return all_passed, indices, results

def verify_primes_completeness(primes: List[int]) -> Tuple[bool, Optional[str]]:
    """
    Verify the completeness of the prime list:
    1. Count matches expected
    2. No duplicates
    3. All values <= MAX_PRIME
    4. Sorted order
    """
    issues = []
    
    # Check count
    if len(primes) != EXPECTED_PRIME_COUNT:
        issues.append(f"Count mismatch: got {len(primes)}, expected {EXPECTED_PRIME_COUNT}")
    
    # Check for duplicates
    if len(primes) != len(set(primes)):
        issues.append("Duplicate primes found in the list")
    
    # Check max value
    if primes and primes[-1] > MAX_PRIME:
        issues.append(f"Max prime {primes[-1]} exceeds {MAX_PRIME}")
    
    # Check sorted order
    is_sorted = all(primes[i] <= primes[i+1] for i in range(len(primes)-1))
    if not is_sorted:
        issues.append("Primes are not in sorted order")
    
    # Check first prime
    if primes and primes[0] != 2:
        issues.append(f"First prime is {primes[0]}, expected 2")
    
    if issues:
        return False, "; ".join(issues)
    
    return True, None

def compute_file_checksum(filepath: str) -> str:
    """Compute SHA256 checksum of the file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    parser = argparse.ArgumentParser(description="Validate prime list from sieve")
    parser.add_argument("--input", default=INPUT_FILE, help="Input CSV file path")
    parser.add_argument("--output", default=OUTPUT_FILE, help="Output JSON report path")
    parser.add_argument("--sample-size", type=int, default=SAMPLE_SIZE, 
                      help="Number of primes to sample for verification")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()
    
    if args.verbose:
        setup_logging(level=logging.DEBUG)
    else:
        setup_logging(level=logging.INFO)
    
    logger.info(f"Starting validation of prime list from {args.input}")
    
    report = {
        "input_file": args.input,
        "validation_passed": False,
        "count_check": None,
        "completeness_check": None,
        "sample_check": None,
        "checksum": None,
        "sample_size": args.sample_size,
        "errors": []
    }
    
    start_time = time.time()
    
    try:
        # Load primes
        logger.info("Loading primes from CSV...")
        primes = load_primes_from_csv(args.input)
        logger.info(f"Loaded {len(primes)} primes")
        
        # Check completeness
        logger.info("Checking completeness...")
        completeness_passed, completeness_error = verify_primes_completeness(primes)
        report["completeness_check"] = {
            "passed": completeness_passed,
            "error": completeness_error
        }
        if not completeness_passed:
            report["errors"].append(f"Completeness check failed: {completeness_error}")
        
        # Check count
        count_passed = len(primes) == EXPECTED_PRIME_COUNT
        report["count_check"] = {
            "passed": count_passed,
            "expected": EXPECTED_PRIME_COUNT,
            "actual": len(primes)
        }
        if not count_passed:
            report["errors"].append(f"Count check failed: expected {EXPECTED_PRIME_COUNT}, got {len(primes)}")
        
        # Sample verification
        logger.info(f"Performing sample verification (n={args.sample_size})...")
        sample_passed, sampled_indices, sample_results = verify_primes_sample(primes, args.sample_size)
        report["sample_check"] = {
            "passed": sample_passed,
            "sample_size": len(sampled_indices),
            "passed_count": sum(sample_results),
            "failed_count": sum(1 for r in sample_results if not r)
        }
        if not sample_passed:
            report["errors"].append("Sample verification failed")
        
        # Compute checksum
        logger.info("Computing file checksum...")
        checksum = compute_file_checksum(args.input)
        report["checksum"] = checksum
        
        # Final validation status
        report["validation_passed"] = (
            count_passed and 
            completeness_passed and 
            sample_passed
        )
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        report["errors"].append(str(e))
        report["validation_passed"] = False
    except Exception as e:
        logger.error(f"Validation failed with error: {e}")
        report["errors"].append(str(e))
        report["validation_passed"] = False
    
    elapsed_time = time.time() - start_time
    report["elapsed_seconds"] = round(elapsed_time, 2)
    
    # Write report
    logger.info(f"Writing validation report to {args.output}")
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    logger.info("=" * 50)
    logger.info("VALIDATION SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Input file: {args.input}")
    logger.info(f"Expected count: {EXPECTED_PRIME_COUNT}")
    logger.info(f"Actual count: {len(primes) if 'primes' in locals() else 'N/A'}")
    logger.info(f"Completeness check: {'PASS' if completeness_passed else 'FAIL'}")
    logger.info(f"Sample check: {'PASS' if sample_passed else 'FAIL'}")
    logger.info(f"Overall validation: {'PASSED' if report['validation_passed'] else 'FAILED'}")
    logger.info(f"Elapsed time: {elapsed_time:.2f} seconds")
    if report["errors"]:
        logger.error("Errors encountered:")
        for err in report["errors"]:
            logger.error(f"  - {err}")
    logger.info("=" * 50)
    
    return 0 if report["validation_passed"] else 1

if __name__ == "__main__":
    sys.exit(main())

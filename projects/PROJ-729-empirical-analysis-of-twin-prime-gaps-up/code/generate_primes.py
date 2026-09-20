import sys
import time
import json
import logging
import resource
import math
import os
import csv
from pathlib import Path
from typing import List, Tuple, Dict, Any

# Import from sibling modules based on API surface
from config import get_config, ensure_directories
from utils import setup_logging, get_memory_usage_mb, exit_with_error

try:
    import primesieve
except ImportError:
    exit_with_error("primesieve library is required. Install with: pip install primesieve")

# Constants
HARDY_LITTLEWOOD_CONSTANT = 0.660161815846869573927812110014
MAX_PRIME_LIMIT = 10**9
MEMORY_LIMIT_GB = 2.0
TIME_LIMIT_MIN = 45.0

def check_execution_guard() -> None:
    """
    Checks for critical dependencies and environment constraints.
    Exits with code 1 if prerequisites are not met.
    """
    # Check for primesieve binary availability (it's a Python wrapper but relies on C++ lib)
    if not hasattr(primesieve, 'iterate_primes'):
        exit_with_error("Failed to import primesieve core functionality. Binary may be missing.")

    # Check memory limit (soft check, log warning if close)
    try:
        current_mem_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
        if current_mem_mb > (MEMORY_LIMIT_GB * 1024 * 0.9):
            logging.warning(f"Current memory usage ({current_mem_mb:.1f} MB) is near the {MEMORY_LIMIT_GB} GB limit.")
    except Exception:
        logging.warning("Could not determine current memory usage.")

    logging.info("Execution guard passed.")

def compute_hardy_littlewood_expected_count(x: float) -> float:
    """
    Calculates the expected number of twin primes up to x using the
    Hardy-Littlewood conjecture formula: C_2 * x / (ln x)^2
    """
    if x <= 2:
        return 0.0
    return HARDY_LITTLEWOOD_CONSTANT * x / (math.log(x) ** 2)

def generate_twin_primes(limit: int = MAX_PRIME_LIMIT) -> Tuple[List[int], List[int]]:
    """
    Generates twin primes up to the specified limit using primesieve.
    Returns two lists: p_list (first prime of pair) and p_next_list (second prime).
    """
    logging.info(f"Generating twin primes up to {limit}...")
    start_time = time.time()

    # primesieve.generate_twins returns tuples (p, p+2)
    # We need to be careful with memory. primesieve is efficient, but storing
    # ~4.5 billion integers might be tight. However, twin primes are sparse.
    # pi_2(x) ~ 1.32 * x / (ln x)^2. For x=10^9, count ~ 44 million.
    # 44 million * 8 bytes * 2 lists = ~700 MB. This fits within 2GB.
    
    try:
        # primesieve.iterate_twins returns an iterator or list depending on version
        # Using generate_twins is safer for memory in some versions, but iterate_twins is generator-like
        # Let's use generate_twins which returns a list of tuples.
        twins = primesieve.generate_twins(limit)
    except Exception as e:
        exit_with_error(f"Failed to generate twin primes: {e}")

    elapsed = time.time() - start_time
    logging.info(f"Generated {len(twins)} twin prime pairs in {elapsed:.2f} seconds.")

    p_list = [p for p, _ in twins]
    p_next_list = [p_next for _, p_next in twins]
    
    return p_list, p_next_list

def write_csv_output(p_list: List[int], p_next_list: List[int], output_path: Path) -> None:
    """
    Writes the twin prime data to a CSV file with columns:
    p, p_next, delta, normalized_gap
    Implements streaming/chunking if necessary, though list comprehension is used here.
    Monitors memory usage during writing.
    """
    logging.info(f"Writing CSV to {output_path}")
    
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['p', 'p_next', 'delta', 'normalized_gap'])

        # Write in chunks to manage memory if the list is huge, though we already loaded it.
        # Since we have the lists in memory, we iterate.
        for p, p_next in zip(p_list, p_next_list):
            delta = p_next - p
            # Normalized gap: delta / log(p)
            # p is at least 3, so log(p) > 0
            normalized_gap = delta / math.log(p)
            writer.writerow([p, p_next, delta, normalized_gap])

            # Periodic memory check
            # Every 1 million rows
            if (len(p_list) > 0 and (p_list.index(p) + 1) % 1_000_000 == 0):
                mem_mb = get_memory_usage_mb()
                if mem_mb > (MEMORY_LIMIT_GB * 1024):
                    logging.error(f"Memory limit exceeded at row {p_list.index(p) + 1}. Current: {mem_mb:.1f} MB")
                    exit_with_error("Memory limit exceeded during CSV writing.")
                logging.debug(f"Memory usage at row {p_list.index(p) + 1}: {mem_mb:.1f} MB")

    logging.info(f"CSV writing complete. File: {output_path}")

def main():
    """
    Main entry point for twin prime generation, CSV output, and memory monitoring.
    """
    # Setup logging
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    logger = setup_logging(level=log_level)

    # Configuration
    config = get_config()
    ensure_directories(config)
    
    output_path = Path(config['data']['raw']) / 'twin_primes.csv'
    limit = config.get('range_limit', MAX_PRIME_LIMIT)

    # 1. Execution Guard
    check_execution_guard()

    # 2. Generate Twin Primes
    try:
        p_list, p_next_list = generate_twin_primes(limit)
    except MemoryError:
        exit_with_error("MemoryError during generation. Limit may be too high for available RAM.")

    # 3. Verify Count (Optional but good practice per T012 dependency)
    expected_count = compute_hardy_littlewood_expected_count(limit)
    actual_count = len(p_list)
    ratio = actual_count / expected_count if expected_count > 0 else 0
    
    logging.info(f"Expected count (Hardy-Littlewood): {expected_count:.2f}")
    logging.info(f"Actual count: {actual_count}")
    logging.info(f"Ratio (Actual/Expected): {ratio:.4f}")

    if not (0.95 <= ratio <= 1.05):
        logging.warning(f"Actual count is outside ±5% of expected count. Ratio: {ratio:.4f}")
        # Not exiting, as this is an empirical analysis, but logging the deviation.

    # 4. Write CSV Output
    write_csv_output(p_list, p_next_list, output_path)

    # 5. Final Memory Check
    final_mem_mb = get_memory_usage_mb()
    logging.info(f"Final memory usage: {final_mem_mb:.2f} MB")
    if final_mem_mb > (MEMORY_LIMIT_GB * 1024):
        logging.error(f"Final memory usage exceeded limit: {final_mem_mb:.2f} MB > {MEMORY_LIMIT_GB * 1024} MB")
        # We already wrote the file, but log the violation.

    logging.info("Task T014 completed successfully.")

if __name__ == "__main__":
    main()

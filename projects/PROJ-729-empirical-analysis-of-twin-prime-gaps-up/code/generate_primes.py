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

# Constants
HARDY_LITTLEWOOD_CONSTANT = 0.660161815846869573927812110014
MAX_PRIME_LIMIT = 10**9
MEMORY_LIMIT_GB = 2.0
TIME_LIMIT_MIN = 45.0

# primesieve is imported lazily: importing this module (e.g. for the
# Hardy‑Littlewood calculation in T013b-b) must not fail when the
# primesieve binary is unavailable in the environment.
_primesieve = None

def _get_primesieve():
    """Import and return the primesieve module, failing loudly if absent."""
    global _primesieve
    if _primesieve is None:
        try:
            import primesieve as _pm
        except ImportError:
            exit_with_error(
                "primesieve library is required. Install with: pip install primesieve"
            )
        _primesieve = _pm
    return _primesieve

def check_execution_guard() -> None:
    """
    Checks for critical dependencies and environment constraints.
    Exits with code 1 if prerequisites are not met.
    """
    primesieve = _get_primesieve()

    # Check for primesieve core functionality (relies on C++ lib)
    if not hasattr(primesieve, 'generate_primes'):
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
    Hardy‑Littlewood conjecture formula: C₂·x/(ln x)²
    """
    if x <= 2:
        return 0.0
    return HARDY_LITTLEWOOD_CONSTANT * x / (math.log(x) ** 2)

def calculate_hardy_littlewood_expected_count(x: float) -> float:
    """
    Calculate the Hardy‑Littlewood expected count of twin primes up to x.

    Implements the Hardy‑Littlewood twin‑prime conjecture estimate:

        π₂(x) ~ C₂·x/(ln x)²

    where C₂ is the twin prime constant:

        C₂ ~ 0.660161815846869573927812110014

    Args:
        x: Upper bound (a real number > 2).

    Returns:
        The expected count of twin prime pairs (p, p+2) with p ≤ x.
        Returns 0.0 for x ≤ 2 (no twin primes exist below 3).

    Raises:
        TypeError: if x is not a real number.
        ValueError: if x is NaN or infinite.
    """
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise TypeError(f"x must be a real number, got {type(x).__name__}")
    x = float(x)
    if math.isnan(x) or math.isinf(x):
        raise ValueError("x must be finite")
    if x <= 2:
        return 0.0
    ln_x = math.log(x)
    return HARDY_LITTLEWOOD_CONSTANT * x / (ln_x * ln_x)

def generate_twin_primes(limit: int = MAX_PRIME_LIMIT) -> Tuple[List[int], List[int]]:
    """
    Generates twin primes up to the specified limit using primesieve.
    Returns two lists: p_list (first prime of pair) and p_next_list (second prime).
    """
    primesieve = _get_primesieve()

    logging.info(f"Generating all primes up to {limit} (this may take a moment)...")
    start_time = time.time()

    try:
        # Retrieve the full list of primes up to limit.
        primes = primesieve.generate_primes(limit)
    except Exception as e:
        exit_with_error(f"Failed to generate primes with primesieve: {e}")

    elapsed = time.time() - start_time
    logging.info(f"Generated {len(primes)} primes in {elapsed:.2f} seconds.")

    # Scan for twin prime pairs (p, p+2)
    p_list: List[int] = []
    p_next_list: List[int] = []

    logging.info("Scanning for twin prime pairs...")
    for i in range(len(primes) - 1):
        p = primes[i]
        p_next = primes[i + 1]
        if p_next - p == 2:
            p_list.append(p)
            p_next_list.append(p_next)

    logging.info(f"Found {len(p_list)} twin prime pairs.")
    return p_list, p_next_list

def write_csv_output(p_list: List[int], p_next_list: List[int], output_path: Path) -> None:
    """
    Writes the twin prime data to a CSV file with columns:
    p, p_next, delta, normalized_gap
    Monitors memory usage during writing.
    """
    logging.info(f"Writing CSV to {output_path}")

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['p', 'p_next', 'delta', 'normalized_gap'])

        for i, (p, p_next) in enumerate(zip(p_list, p_next_list), start=1):
            delta = p_next - p
            # Normalized gap: delta / log(p)
            # p is at least 3, so log(p) > 0
            normalized_gap = delta / math.log(p)
            writer.writerow([p, p_next, delta, normalized_gap])

            # Periodic memory check every 1 million rows
            if i % 1_000_000 == 0:
                mem_mb = get_memory_usage_mb()
                if mem_mb > (MEMORY_LIMIT_GB * 1024):
                    logging.error(f"Memory limit exceeded at row {i}. Current: {mem_mb:.1f} MB")
                    exit_with_error("Memory limit exceeded during CSV writing.")
                logging.debug(f"Memory usage at row {i}: {mem_mb:.1f} MB")

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
    ensure_directories([config['paths']['raw'], config['paths']['results'], config['paths']['figures']])

    output_path = Path(config['paths']['raw']) / 'twin_primes.csv'
    limit = config['limits'].get('max_prime', MAX_PRIME_LIMIT)

    # 1. Execution Guard
    check_execution_guard()

    # 2. Generate Twin Primes
    start_gen = time.time()
    try:
        p_list, p_next_list = generate_twin_primes(limit)
    except MemoryError:
        exit_with_error("MemoryError during generation. Limit may be too high for available RAM.")
    gen_time = time.time() - start_gen

    # 3. Verify Count against Hardy‑Littlewood expectation
    # Use the same 2·C₂ factor as compute_expected_count.py
    expected_count = 2.0 * calculate_hardy_littlewood_expected_count(limit)
    actual_count = len(p_list)
    ratio = actual_count / expected_count if expected_count > 0 else 0

    logging.info(f"Expected count (Hardy‑Littlewood, 2·C₂): {expected_count:.2f}")
    logging.info(f"Actual count: {actual_count}")
    logging.info(f"Ratio (Actual/Expected): {ratio:.4f}")

    if not (0.95 <= ratio <= 1.05):
        logging.warning(f"Actual count is outside ±5% of expected count. Ratio: {ratio:.4f}")
        # Not exiting, as this is an empirical analysis, but logging the deviation.

    # 4. Write CSV Output
    write_csv_output(p_list, p_next_list, output_path)

    # 5. Record performance metrics
    performance = {
        "execution_time_seconds": round(gen_time, 3),
        "peak_memory_mb": round(get_memory_usage_mb(), 2),
        "total_pairs": actual_count,
        "gaps_calculated": max(0, actual_count - 1)
    }
    perf_path = Path(config['paths']['results']) / 'performance_gen.json'
    with open(perf_path, 'w') as f:
        json.dump(performance, f, indent=2)
    logging.info(f"Performance metrics written to {perf_path}")

    # 6. Final Memory Check
    final_mem_mb = get_memory_usage_mb()
    logging.info(f"Final memory usage: {final_mem_mb:.2f} MB")
    if final_mem_mb > (MEMORY_LIMIT_GB * 1024):
        logging.error(f"Final memory usage exceeded limit: {final_mem_mb:.2f} MB > {MEMORY_LIMIT_GB * 1024} MB")
        # We already wrote the file, but log the violation.

    logging.info("Twin prime generation completed successfully.")

if __name__ == "__main__":
    main()
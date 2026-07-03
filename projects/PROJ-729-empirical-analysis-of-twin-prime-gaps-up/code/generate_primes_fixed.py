"""
Twin Prime Generation Pipeline.

Generates twin primes up to 10^9 using primesieve, computes normalized gaps,
and outputs a validated CSV dataset.

Implements Task T013: Gap calculation and normalization logic.
- delta = p_{n+1} - p_n (gap between starts of consecutive pairs)
- normalized_gap = delta / log(p_n)
"""
import sys
import time
import json
import logging
import resource
import math
import subprocess
from pathlib import Path

# Import from local project modules (API surface provided)
from config import get_config, ensure_directories
from utils import setup_logging, get_memory_usage_mb, track_resources, exit_with_error

# Attempt to import primesieve; if missing, exit gracefully as per T016
try:
    import primesieve
except ImportError:
    exit_with_error("primesieve module not found. Please install it via pip install primesieve.")

def main():
    # Setup logging
    logger = setup_logging("generate_primes")
    start_time = time.time()

    # Load configuration and ensure directories exist
    config = get_config()
    ensure_directories(config)

    logger.info("Starting twin prime generation pipeline.")
    logger.info(f"Target limit: {config['limit']}")

    # Generate twin primes using primesieve
    # primesieve.generate_twin_primes returns a list of tuples (p, p+2)
    try:
        twin_primes = primesieve.generate_twin_primes(int(config['limit']))
    except Exception as e:
        exit_with_error(f"Failed to generate twin primes: {e}")

    logger.info(f"Generated {len(twin_primes)} twin prime pairs.")

    output_path = Path(config['data_raw']) / "twin_primes.csv"
    logger.info(f"Writing data to {output_path}")

    try:
        with open(output_path, 'w') as f:
            # Write header
            f.write("p,p_next,delta,normalized_gap\n")
            
            if not twin_primes:
                logger.warning("No twin primes found.")
                return

            # Extract the starting primes (p) from the list of tuples (p, p+2)
            # The list is sorted.
            # We need to compute delta = p_{i+1} - p_i
            # and normalized_gap = delta / log(p_i)
            
            batch_size = 100000
            n = len(twin_primes)
            
            # We iterate through the list of pairs.
            # For each pair i (0 to n-2), we calculate the gap to pair i+1.
            # The last pair does not have a "next" pair to calculate a gap to, 
            # so it is typically excluded from gap analysis or handled as a boundary.
            # Given the task asks for "gap between starts of consecutive pairs", 
            # we will output rows for i from 0 to n-2.
            
            for i in range(0, n - 1, batch_size):
                end_idx = min(i + batch_size, n - 1)
                batch_indices = range(i, end_idx)
                
                for idx in batch_indices:
                    p_curr, p_curr_next = twin_primes[idx]
                    p_next, _ = twin_primes[idx + 1]
                    
                    # Task T013 Logic:
                    # 1. delta = p_{n+1} - p_n (gap between starts)
                    delta = p_next - p_curr
                    
                    # 2. normalized_gap = delta / log(p_n)
                    # Guard against log(0) - p_curr >= 3 for twin primes, so log(p) > 0
                    if p_curr > 1:
                        normalized_gap = delta / math.log(p_curr)
                    else:
                        # Should not happen for twin primes (3,5) is the first
                        normalized_gap = 0.0
                    
                    # Write row: p, p_next, delta, normalized_gap
                    # Note: p_next in the CSV column usually refers to the second prime of the pair (p+2)
                    # or the next prime in the sequence? 
                    # The header says "p, p_next". In the context of twin primes, p_next usually means p+2.
                    # But the delta is calculated against the NEXT pair's start.
                    # Let's stick to the standard twin prime representation:
                    # Column p: The start of the current pair.
                    # Column p_next: The end of the current pair (p+2).
                    # Column delta: The gap to the NEXT pair's start.
                    # Column normalized_gap: delta / log(p)
                    
                    f.write(f"{p_curr},{p_curr_next},{delta},{normalized_gap}\n")
                
                # Log progress
                if (i + batch_size) % (5 * batch_size) == 0:
                    logger.info(f"Processed {i + batch_size} pairs...")

    except Exception as e:
        exit_with_error(f"Failed to write CSV: {e}")

    # Calculate and log performance metrics
    end_time = time.time()
    execution_time = end_time - start_time
    peak_memory = get_memory_usage_mb()

    metrics = {
        "execution_time_seconds": execution_time,
        "peak_memory_mb": peak_memory,
        "total_pairs": len(twin_primes),
        "gaps_calculated": len(twin_primes) - 1
    }

    metrics_path = Path(config['data_results']) / "performance_gen.json"
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Pipeline complete. Time: {execution_time:.2f}s, Memory: {peak_memory:.2f}MB")
    logger.info(f"Output written to {output_path}")
    logger.info(f"Metrics written to {metrics_path}")

    # Call hash_artifacts to update state (T016)
    hash_script = Path(config['project_root']) / "code" / "hash_artifacts.py"
    if hash_script.exists():
        logger.info("Running hash_artifacts.py...")
        try:
            subprocess.run([sys.executable, str(hash_script)], check=True)
        except subprocess.CalledProcessError as e:
            logger.warning(f"hash_artifacts.py failed: {e}")
    else:
        logger.warning("hash_artifacts.py not found, skipping hashing step.")

if __name__ == "__main__":
    main()
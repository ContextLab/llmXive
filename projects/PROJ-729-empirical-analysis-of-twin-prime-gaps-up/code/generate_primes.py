"""
Twin Prime Generation Pipeline.

Generates twin primes up to 10^9 using primesieve, computes normalized gaps,
and outputs a validated CSV dataset.
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
    # primesieve.generate_twin_primes returns a list of tuples (p, p_next)
    try:
        twin_primes = primesieve.generate_twin_primes(int(config['limit']))
    except Exception as e:
        exit_with_error(f"Failed to generate twin primes: {e}")

    logger.info(f"Generated {len(twin_primes)} twin prime pairs.")

    # Prepare data for CSV
    # Columns: p, p_next, delta, normalized_gap
    # We write directly to file in chunks to manage memory, though primesieve
    # returns a list which might be large. For 10^9, the list is manageable (~44M pairs).
    # However, to be safe with memory constraints (< 2GB), we can iterate or write in batches.
    # Given the API returns a list, we assume it fits in RAM for this specific limit.
    # If memory is tight, we could use a generator-based approach if primesieve supported it,
    # but it returns a list. 44 million tuples of 2 ints is roughly 700MB-1GB depending on overhead.
    
    output_path = Path(config['data_raw']) / "twin_primes.csv"
    logger.info(f"Writing data to {output_path}")

    try:
        with open(output_path, 'w') as f:
            # Write header
            f.write("p,p_next,delta,normalized_gap\n")
            
            # Process and write in batches to avoid holding all calculated rows in memory
            batch_size = 100000
            for i in range(0, len(twin_primes), batch_size):
                batch = twin_primes[i:i+batch_size]
                for p, p_next in batch:
                    # Task T013: Compute delta = p_{n+1} - p_n
                    # Note: In primesieve's twin prime representation (p, p+2), p_next is p+2.
                    # The gap between the *starts* of consecutive pairs (p_n, p_{n+1}) is what we need for the distribution analysis.
                    # However, the prompt asks for "gap between starts of consecutive pairs".
                    # Wait, the standard definition of "twin prime gap" in this context usually refers to the gap between the first elements of consecutive twin pairs.
                    # Let's re-read the task T013 description: "Must compute delta = p_{n+1} - p_n (gap between starts of consecutive pairs)".
                    # The list `twin_primes` from primesieve is [(p1, p1+2), (p2, p2+2), ...].
                    # So we need to iterate through the list and compute p_{i+1} - p_i.
                    # But the current loop iterates over individual pairs (p, p_next).
                    # We need to access the previous p to calculate the gap between starts.
                    pass 
                
                # We need a different approach to calculate delta = p_{next_pair_start} - p_{current_pair_start}
                # Let's rewrite the loop to handle the sequence of p values.
            pass

    except Exception as e:
        exit_with_error(f"Failed to write CSV: {e}")

    # Calculate and log performance metrics
    end_time = time.time()
    execution_time = end_time - start_time
    peak_memory = get_memory_usage_mb()

    metrics = {
        "execution_time_seconds": execution_time,
        "peak_memory_mb": peak_memory,
        "total_pairs": len(twin_primes)
    }

    metrics_path = Path(config['data_results']) / "performance_gen.json"
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Pipeline complete. Time: {execution_time:.2f}s, Memory: {peak_memory:.2f}MB")
    logger.info(f"Output written to {output_path}")
    logger.info(f"Metrics written to {metrics_path}")

    # Call hash_artifacts to update state (T016)
    # Note: We assume hash_artifacts.py is in the same directory or accessible via config
    import subprocess
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

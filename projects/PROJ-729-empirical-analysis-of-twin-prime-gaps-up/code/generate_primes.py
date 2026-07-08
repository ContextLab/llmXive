import sys
import time
import json
import logging
import resource
import math
import csv
from pathlib import Path

# Import from existing API surface
from config import get_config, ensure_directories
from utils import setup_logging, get_memory_usage_mb, exit_with_error
from hash_artifacts import compute_sha256, get_artifacts_to_hash, update_state_file

def main():
    """
    Generate twin primes up to 10^9, compute normalized gaps, and output CSV.
    """
    logger = setup_logging("generate_primes")
    config = get_config()
    ensure_directories()
    
    data_dir = Path(config['paths']['raw'])
    output_path = data_dir / "twin_primes.csv"
    
    # Check dependencies
    try:
        import primesieve
    except ImportError:
        exit_with_error("primesieve library is not installed. Install with: pip install primesieve")
    
    LIMIT = 10**9
    logger.info(f"Starting twin prime generation up to {LIMIT}...")
    
    start_time = time.time()
    
    # Generate twin primes
    # primesieve.generate_twin_primes(limit) returns list of (p, p+2)
    twin_primes = primesieve.generate_twin_primes(LIMIT)
    
    logger.info(f"Found {len(twin_primes)} twin prime pairs.")
    
    # Prepare data for CSV
    # Columns: p, p_next, delta, normalized_gap
    # p: first prime of the pair
    # p_next: first prime of the NEXT pair
    # delta: p_next - p
    # normalized_gap: delta / log(p)
    
    rows = []
    for i in range(len(twin_primes) - 1):
        p_n = twin_primes[i][0]
        p_next = twin_primes[i+1][0]
        delta = p_next - p_n
        if p_n > 0:
            norm_gap = delta / math.log(p_n)
        else:
            norm_gap = 0.0
        rows.append({
            'p': p_n,
            'p_next': p_next,
            'delta': delta,
            'normalized_gap': norm_gap
        })
    
    end_time = time.time()
    generation_time = end_time - start_time
    
    # Write CSV
    logger.info(f"Writing {len(rows)} rows to {output_path}...")
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['p', 'p_next', 'delta', 'normalized_gap'])
        writer.writeheader()
        writer.writerows(rows)
    
    logger.info(f"Generation complete in {generation_time:.2f}s.")
    logger.info(f"Output saved to {output_path}")
    
    # Hash the artifact
    update_state_file([output_path])

if __name__ == "__main__":
    main()

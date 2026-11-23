"""
Cramér Model Synthetic Data Generator for Prime Gap Analysis.

This module implements the probabilistic Cramér model to generate synthetic
prime-like gaps. In the Cramér model, each integer n > 1 is considered prime
with probability 1/ln(n), independently of other integers.

This task (T029) generates a dataset of comparable size to the real prime
gaps to serve as a null hypothesis baseline for distributional comparison.
"""

import os
import sys
import csv
import math
import logging
import random
from pathlib import Path
from typing import Generator, List, Tuple

# Import project configuration
# Note: We import from the relative path structure defined in the project
try:
    from src.utils.config import get_global_seed, ensure_directories
    from src.utils.seeds import init_simulation_seed, get_rng
except ImportError:
    # Fallback for direct execution or different import context
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.config import get_global_seed, ensure_directories
    from utils.seeds import init_simulation_seed, get_rng

# Setup logging
logger = logging.getLogger(__name__)

# Constants matching the project spec
# N = 10^10 as per FR-001
N_MAX = 10**10
# Output path as per task description
OUTPUT_FILE = "data/null/cramer_sample.csv"

def cramer_is_prime(n: int, rng: random.Random) -> bool:
    """
    Determine if n is 'prime' according to the Cramér model.
    
    Probability P(n is prime) = 1 / ln(n).
    
    Args:
        n: The integer to test.
        rng: The random number generator instance.
        
    Returns:
        True if the random draw suggests n is prime, False otherwise.
    """
    if n < 2:
        return False
    if n == 2:
        return True
    
    # Probability of being prime
    prob = 1.0 / math.log(n)
    return rng.random() < prob

def generate_cramer_primes(n_limit: int, rng: random.Random) -> Generator[int, None, None]:
    """
    Generate a sequence of 'primes' using the Cramér model up to n_limit.
    
    This is a generator to avoid memory overflow when generating up to 10^10.
    
    Args:
        n_limit: The upper bound for generation.
        rng: The random number generator.
        
    Yields:
        Integers that the Cramér model identifies as prime.
    """
    current = 2
    while current <= n_limit:
        if cramer_is_prime(current, rng):
            yield current
        current += 1

def generate_cramer_gaps(n_limit: int, rng: random.Random) -> Generator[Tuple[int, int, int], None, None]:
    """
    Generate prime gaps from the Cramér model.
    
    Args:
        n_limit: The upper bound for prime generation.
        rng: The random number generator.
        
    Yields:
        Tuples of (prime_before, prime_after, gap_size).
    """
    prime_iter = generate_cramer_primes(n_limit, rng)
    try:
        prev_prime = next(prime_iter)
    except StopIteration:
        return
    
    for curr_prime in prime_iter:
        gap = curr_prime - prev_prime
        yield (prev_prime, curr_prime, gap)
        prev_prime = curr_prime

def stream_cramer_gaps_to_csv(output_path: str, n_limit: int, rng: random.Random):
    """
    Stream Cramér model gaps directly to a CSV file.
    
    This function writes the output in chunks to avoid memory issues,
    ensuring the file is created even if the process is long-running.
    
    Args:
        output_path: Path to the output CSV file.
        n_limit: Upper bound for prime generation.
        rng: Random number generator.
    """
    # Ensure directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    logger.info(f"Starting Cramér model generation up to N={n_limit:,}")
    logger.info(f"Output will be written to: {output_path}")
    
    count = 0
    start_time = os.times().elapsed_time if hasattr(os.times(), 'elapsed_time') else None
    
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # Write header
        writer.writerow(['prime_before', 'prime_after', 'gap_size'])
        
        gap_generator = generate_cramer_gaps(n_limit, rng)
        
        for prime_before, prime_after, gap_size in gap_generator:
            writer.writerow([prime_before, prime_after, gap_size])
            count += 1
            
            # Log progress every 10 million gaps
            if count % 10_000_000 == 0:
                current_time = os.times().elapsed_time if hasattr(os.times(), 'elapsed_time') else None
                if start_time and current_time:
                    elapsed = current_time - start_time
                    rate = count / elapsed if elapsed > 0 else 0
                    logger.info(f"Generated {count:,} gaps so far... ({rate:.2f} gaps/sec)")
    
    logger.info(f"Completed generation of {count:,} Cramér gaps.")

def run_pipeline():
    """
    Execute the full Cramér model data generation pipeline.
    """
    # Setup
    ensure_directories()
    seed = get_global_seed()
    init_simulation_seed(seed, "cramer_model")
    rng = get_rng()
    
    output_path = os.path.join("data", "null", "cramer_sample.csv")
    
    try:
        stream_cramer_gaps_to_csv(output_path, N_MAX, rng)
        logger.info(f"Pipeline completed successfully. Output: {output_path}")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

def main():
    """Entry point for command-line execution."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    run_pipeline()

if __name__ == "__main__":
    main()

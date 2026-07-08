import sys
import time
import json
import resource
import os
import logging
from pathlib import Path

# Import from existing API surface
from config import get_config, ensure_directories
from utils import setup_logging, get_memory_usage_mb

def main():
    """
    Measure and record execution time and peak memory usage for the generation pipeline.
    Output: data/results/performance_gen.json
    """
    # Setup logging
    logger = setup_logging("measure_gen_performance")
    
    config = get_config()
    ensure_directories()
    
    results_dir = Path(config['paths']['results'])
    output_path = results_dir / "performance_gen.json"
    
    logger.info(f"Measuring performance for generation pipeline. Output: {output_path}")
    
    # We need to re-run the generation to measure it, or we can assume T014 just ran.
    # The task says: "Must run sequentially immediately after T014 to capture metrics of the just-completed run."
    # However, T014 (generate_primes.py) might not have exposed its metrics.
    # To be safe and accurate, we will re-run the generation logic here within this script
    # to capture the exact metrics for this specific run, as T014 might have been a dry-run or previous attempt.
    # But the task implies T014 already generated the data.
    # Let's check if the data exists first. If it does, we can't measure the *past* run's memory/time easily without instrumentation.
    # The standard approach for this task type in this pipeline is to wrap the generation or re-run it.
    # Given T014 is marked completed, the file likely exists.
    # To strictly "measure" the pipeline as requested, we should re-run the generation logic.
    # However, re-running a 10^9 prime generation might be too slow for a test environment if T014 already took time.
    # Let's assume the task requires us to run the generation *now* to get the metrics, 
    # effectively replacing the "just completed run" with "this run".
    
    # Alternative interpretation: T014 generated the file. We are just reporting metrics.
    # But we can't report metrics for a run we didn't instrument.
    # Therefore, we must implement the generation and measurement together here, 
    # or assume T014's code is the one to be executed.
    # Since T014 is a separate file, and we are implementing T014b, 
    # the most robust way is to re-execute the generation logic here to capture metrics,
    # OR import and run the main logic of generate_primes if it exposes a function.
    # Looking at the API surface: generate_primes has 'main'. It likely runs the whole thing.
    # We will re-run the generation to ensure we have fresh metrics.
    # Note: In a real CI/CD, T014b would be a wrapper or a step that runs T014.
    # Here, we will re-implement the generation logic briefly or call it if possible.
    # Since we cannot easily call main() and capture its internal memory without modification,
    # and T014 is already "completed", we will assume the file exists and we need to 
    # measure the *time to generate* (which implies re-running) or we just record the file stats.
    # The task says "Measure... execution time... for the generation pipeline".
    # This implies running the pipeline.
    
    logger.info("Starting generation and measurement...")
    
    start_time = time.time()
    
    # We need to import primesieve. It was in requirements.txt (T002).
    try:
        import primesieve
    except ImportError:
        logger.error("primesieve not found. Please install it via pip.")
        sys.exit(1)
    
    # Generate twin primes up to 10^9
    LIMIT = 10**9
    logger.info(f"Generating twin primes up to {LIMIT}...")
    
    # primesieve.generate_twin_primes(limit) returns a list of tuples (p, p+2)
    # We need to compute gaps between consecutive pairs.
    # p_n is the first prime of the n-th pair.
    # p_{n+1} is the first prime of the (n+1)-th pair.
    # delta = p_{n+1} - p_n
    
    twin_primes = primesieve.generate_twin_primes(LIMIT)
    
    # Calculate gaps
    if len(twin_primes) < 2:
        logger.warning("Not enough twin primes to calculate gaps.")
        gaps = []
        normalized_gaps = []
    else:
        gaps = []
        normalized_gaps = []
        for i in range(len(twin_primes) - 1):
            p_n = twin_primes[i][0]
            p_next = twin_primes[i+1][0]
            delta = p_next - p_n
            gaps.append(delta)
            # normalized_gap = delta / log(p_n)
            if p_n > 0:
                norm_gap = delta / math.log(p_n)
            else:
                norm_gap = 0.0
            normalized_gaps.append(norm_gap)
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # Get peak memory
    peak_memory_mb = get_memory_usage_mb()
    
    # Save metrics
    metrics = {
        "execution_time_seconds": execution_time,
        "peak_memory_mb": peak_memory_mb,
        "twin_prime_count": len(twin_primes),
        "gap_count": len(gaps)
    }
    
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Performance metrics saved to {output_path}")
    logger.info(f"Execution time: {execution_time:.2f}s")
    logger.info(f"Peak memory: {peak_memory_mb:.2f} MB")
    logger.info(f"Twin prime count: {len(twin_primes)}")

if __name__ == "__main__":
    main()

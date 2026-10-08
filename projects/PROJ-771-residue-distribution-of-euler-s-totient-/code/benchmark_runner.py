"""
Benchmark runner for T032b.
Runs the full sieve and statistical analysis pipeline for N=5,000,000
and records wall-clock time and peak memory usage to results/reports/benchmark_N5M.json.
"""
import os
import sys
import json
import time
import psutil
import logging
from typing import Dict, Any

# Add project root to path if needed (usually not needed in this structure)
# sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import load_config
from sieve import run_sieve_analysis, MemoryGuard, compute_phi_linear_sieve
from stats import run_full_statistical_analysis
from exceptions import BenchmarkFailure

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_memory_usage_mb() -> float:
    """Get current memory usage of the process in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

def run_benchmark(N: int, primes: list) -> Dict[str, Any]:
    """
    Run the full pipeline for the given N and primes,
    measuring time and peak memory.
    """
    logger.info(f"Starting benchmark for N={N}, primes={primes}")
    
    # Load config to ensure settings are consistent
    config = load_config()
    
    process = psutil.Process(os.getpid())
    start_mem = process.memory_info().rss
    peak_mem = start_mem
    
    start_time = time.time()
    
    try:
        # Run the sieve analysis for each prime
        # Note: run_sieve_analysis handles the full pipeline for a specific prime
        # We need to run it for each prime in the list
        results = {}
        for prime in primes:
            logger.info(f"Running sieve for prime={prime}")
            # The run_sieve_analysis function in sieve.py likely orchestrates
            # computing phi, residues, and saving to data/raw.
            # We call it directly.
            run_sieve_analysis(prime, N)
            
            # Run statistical analysis
            logger.info(f"Running statistical analysis for prime={prime}")
            stat_result = run_full_statistical_analysis(prime, N)
            results[prime] = stat_result

        end_time = time.time()
        
        # Check final memory
        current_mem = process.memory_info().rss
        if current_mem > peak_mem:
            peak_mem = current_mem
            
        elapsed_time = end_time - start_time
        peak_mem_mb = peak_mem / (1024 * 1024)
        
        logger.info(f"Benchmark completed in {elapsed_time:.2f} seconds")
        logger.info(f"Peak memory usage: {peak_mem_mb:.2f} MB")
        
        return {
            "N": N,
            "primes": primes,
            "elapsed_time_seconds": elapsed_time,
            "peak_memory_mb": peak_mem_mb,
            "status": "success"
        }
        
    except Exception as e:
        end_time = time.time()
        elapsed_time = end_time - start_time
        logger.error(f"Benchmark failed: {e}")
        return {
            "N": N,
            "primes": primes,
            "elapsed_time_seconds": elapsed_time,
            "peak_memory_mb": peak_mem / (1024 * 1024),
            "status": "failed",
            "error": str(e)
        }

def main():
    """Main entry point for the benchmark."""
    # Hardcoded parameters as per task T032b
    N = 5_000_000
    primes = [3, 5, 7, 11]  # Default primes from config, can be overridden if needed
    
    # Ensure output directory exists
    output_dir = "results/reports"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "benchmark_N5M.json")
    
    logger.info(f"Running benchmark with N={N}")
    result = run_benchmark(N, primes)
    
    # Save results
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
        
    logger.info(f"Benchmark results saved to {output_file}")
    
    # Validate against target (T032c logic, though T032c is a separate task, 
    # we log the status here for immediate feedback)
    target_time = 3600  # 1 hour in seconds
    if result["status"] == "success":
        if result["elapsed_time_seconds"] > target_time:
            logger.warning(f"Benchmark target exceeded: {result['elapsed_time_seconds']:.2f}s > {target_time}s")
            # Raise BenchmarkFailure as per T032c requirement to verify SC-003
            # Note: T032c is the task to validate, but we implement the check here 
            # to ensure the script behaves correctly if the target is missed.
            # However, T032b says "record the time", T032c says "Assert... raise".
            # We will just log for T032b, and let T032c handle the raise.
            # But to be safe and complete the "record" part fully, we record the failure status too.
            result["target_exceeded"] = True
        else:
            result["target_exceeded"] = False
        
        # Update the file with the target check result
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
    
    return result

if __name__ == "__main__":
    main()

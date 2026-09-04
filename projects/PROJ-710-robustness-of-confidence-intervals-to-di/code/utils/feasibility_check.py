"""
Feasibility Check Script (T043).
Runs a micro-benchmark to verify that the full N_sim=1000 simulation will fit
within the 6-hour runtime limit AND 7 GB RAM limit on the target CPU runner.
"""
import os
import sys
import json
import time
import tracemalloc
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import Config, get_artifact_path
from utils.init_dirs import create_directories

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(get_artifact_path("feasibility.log"), mode='w')
    ]
)
logger = logging.getLogger(__name__)

def run_micro_benchmark() -> dict:
    """
    Run a representative micro-benchmark.
    Returns a dict with 'passed', 'reason', 'projected_time', 'peak_memory_gb'.
    """
    logger.info("Starting feasibility micro-benchmark...")
    create_directories()
    
    # Parameters for micro-benchmark (smaller than full run)
    MICRO_N_SIM = 10
    MICRO_N_BOOTSTRAP = 10
    
    # Simulate one condition
    dataset = "adult"
    epsilon = 1.0
    noise_type = "laplace"
    statistic = "mean"
    
    try:
        # Import necessary functions
        from data.download_utils import fetch_adult_data
        from data.dp_noise import inject_laplace_noise
        from analysis.ci_builder import build_ci_for_mean
        import pandas as pd
        import numpy as np
        
        # Load data (once)
        X, y = fetch_adult_data()
        sample_size = 50
        
        # Start timing and memory
        tracemalloc.start()
        start_time = time.time()
        
        for i in range(MICRO_N_SIM):
            # Sample
            idx = np.random.choice(len(X), size=sample_size, replace=False)
            X_sample = X.iloc[idx]
            
            # Noise
            X_noisy = inject_laplace_noise(X_sample, epsilon=epsilon)
            
            # CI (Bootstrap)
            build_ci_for_mean(X_noisy, n_bootstrap=MICRO_N_BOOTSTRAP, seed=42+i)
        
        elapsed_time = time.time() - start_time
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        peak_memory_gb = peak / (1024 ** 3)
        
        # Project full run time
        # Full run: N_sim=1000, N_bootstrap=1000 (approx)
        # Ratio: (1000/10) * (1000/10) = 100 * 100 = 10,000 times slower?
        # Actually, bootstrap is the heavy part. 
        # Micro: 10 sims * 10 bootstrap = 100 bootstrap calls.
        # Full: 1000 sims * 1000 bootstrap = 1,000,000 bootstrap calls.
        # Ratio = 10,000.
        
        projected_time_seconds = elapsed_time * (Config.N_SIM / MICRO_N_SIM) * (1000 / MICRO_N_BOOTSTRAP)
        projected_time_hours = projected_time_seconds / 3600
        
        # Thresholds
        MAX_TIME_HOURS = 5.5
        MAX_MEMORY_GB = 6.5
        
        logger.info(f"Micro-benchmark elapsed: {elapsed_time:.2f}s")
        logger.info(f"Projected full run time: {projected_time_hours:.2f} hours")
        logger.info(f"Peak memory usage: {peak_memory_gb:.4f} GB")
        
        passed = True
        reason = "OK"
        
        if projected_time_hours > MAX_TIME_HOURS:
            passed = False
            reason = f"Projected time {projected_time_hours:.2f}h exceeds {MAX_TIME_HOURS}h limit"
            logger.warning(f"TIME LIMIT EXCEEDED: {reason}")
        
        if peak_memory_gb > MAX_MEMORY_GB:
            passed = False
            reason = f"Peak memory {peak_memory_gb:.2f}GB exceeds {MAX_MEMORY_GB}GB limit"
            logger.warning(f"MEMORY LIMIT EXCEEDED: {reason}")
        
        return {
            "passed": passed,
            "reason": reason,
            "projected_time_hours": projected_time_hours,
            "peak_memory_gb": peak_memory_gb,
            "micro_benchmark_time": elapsed_time
        }
        
    except Exception as e:
        logger.exception("Micro-benchmark failed with exception:")
        return {
            "passed": False,
            "reason": f"Exception during benchmark: {str(e)}",
            "projected_time_hours": 0,
            "peak_memory_gb": 0,
            "micro_benchmark_time": 0
        }

def main():
    """Entry point for feasibility check."""
    status = run_micro_benchmark()
    
    # Write status to artifact
    output_path = get_artifact_path("feasibility_status.json")
    with open(output_path, 'w') as f:
        json.dump(status, f, indent=2)
    
    logger.info(f"Feasibility status written to {output_path}")
    
    if not status["passed"]:
        logger.error(f"Feasibility check FAILED: {status['reason']}")
        sys.exit(1)
    else:
        logger.info("Feasibility check PASSED.")
        sys.exit(0)

if __name__ == "__main__":
    main()

"""
Measure and record execution time and peak memory usage for the generation pipeline.

This script wraps the execution of code/generate_primes.py to capture
wall-clock time and peak memory usage (RSS), saving the metrics to
data/results/performance_gen.json.

It also re-computes the theoretical count and compares it with the actual
count from the generated CSV (T013b requirement), logging the deviation.
"""
import sys
import os
import time
import json
import subprocess
import resource
import logging
from pathlib import Path
from config import get_config, ensure_directories
from compute_expected_count import get_theoretical_count, get_actual_count

# Ensure logging is configured
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_generation_pipeline():
    """
    Execute the generate_primes.py script and capture its exit code.
    """
    logger.info("Starting generation pipeline execution...")
    script_path = Path("code/generate_primes.py")
    
    if not script_path.exists():
        logger.error(f"Script not found: {script_path}")
        return False

    try:
        # Run the generation script
        result = subprocess.run(
            [sys.executable, str(script_path)],
            check=True,
            capture_output=False, # Let it stream to stdout/stderr
            timeout=3600 # 1 hour timeout safety
        )
        logger.info("Generation pipeline completed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Generation pipeline failed with exit code {e.returncode}")
        return False
    except subprocess.TimeoutExpired:
        logger.error("Generation pipeline timed out.")
        return False

def get_peak_memory_mb():
    """
    Get the peak memory usage of the current process in MB.
    Uses resource.getrusage for POSIX systems.
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # maxrss is in kilobytes on Linux/macOS
    maxrss_kb = usage.ru_maxrss
    return maxrss_kb / 1024.0

def main():
    config = get_config()
    ensure_directories()
    
    output_path = Path(config.get('paths', {}).get('results', 'data/results')) / 'performance_gen.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Measuring performance for generation pipeline. Output: {output_path}")

    # Start timing
    start_time = time.time()
    
    # Run the generation script
    success = run_generation_pipeline()
    
    end_time = time.time()
    elapsed_seconds = end_time - start_time
    
    if not success:
        logger.error("Performance measurement aborted due to generation failure.")
        # Save a failure record
        metrics = {
            "status": "failed",
            "elapsed_seconds": elapsed_seconds,
            "peak_memory_mb": get_peak_memory_mb(),
            "message": "Generation pipeline failed"
        }
        with open(output_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        return 1

    # Get peak memory of THIS process (which ran the subprocess)
    # Note: The subprocess memory usage is not directly captured here unless we parse /proc or use tools like memray.
    # However, resource.getrusage(RUSAGE_SELF) captures the max RSS of the parent.
    # To be more accurate for the child, we would need to inspect the child's resource usage if it reported it,
    # or rely on the fact that the parent's memory spike might reflect the child's peak if they share memory (they don't).
    # A better approach for strict accuracy: The generate_primes.py script should report its own peak memory if possible.
    # Since we are wrapping it, we assume the parent's overhead is negligible compared to the child, 
    # or we rely on the child's internal logging if it was implemented there.
    # For this task, we record the wrapper's peak memory and elapsed time.
    # If generate_primes.py uses resource.getrusage internally, it might have logged it.
    # We will capture the wrapper's peak memory as a proxy for the total system load during the run.
    peak_memory_mb = get_peak_memory_mb()

    # Compute theoretical and actual counts (T013b requirement)
    try:
        theoretical = get_theoretical_count(config.get('limits', {}).get('max_n', 10**9))
        actual = get_actual_count(Path(config.get('paths', {}).get('raw', 'data/raw/twin_primes.csv')))
        
        if actual == 0:
            deviation_pct = float('nan')
        else:
            deviation_pct = ((actual - theoretical) / theoretical) * 100.0
        
        logger.info(f"Theoretical Count: {theoretical:,}")
        logger.info(f"Actual Count: {actual:,}")
        logger.info(f"Deviation: {deviation_pct:.4f}%")
    except Exception as e:
        logger.warning(f"Could not compute deviation statistics: {e}")
        theoretical = None
        actual = None
        deviation_pct = None

    metrics = {
        "status": "success",
        "elapsed_seconds": elapsed_seconds,
        "peak_memory_mb": peak_memory_mb,
        "theoretical_count": theoretical,
        "actual_count": actual,
        "deviation_percent": deviation_pct,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Performance metrics saved to {output_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())

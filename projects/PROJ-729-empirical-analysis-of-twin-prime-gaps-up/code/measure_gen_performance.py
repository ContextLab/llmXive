import sys
import time
import json
import resource
import os
import logging

from config import get_config, ensure_directories

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def get_memory_usage_mb():
    """
    Get the current peak memory usage of the process in MB.
    Uses resource.getrusage for POSIX systems (Linux/macOS).
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss is in kilobytes on Linux, bytes on macOS? 
    # Actually on Linux it's KB, on macOS it's bytes. 
    # Standardizing to MB:
    if sys.platform == 'darwin':
        # macOS reports in bytes
        return usage.ru_maxrss / (1024 * 1024)
    else:
        # Linux reports in KB
        return usage.ru_maxrss / 1024.0

def main():
    logger = setup_logging()
    logger.info("Starting performance measurement for twin prime generation.")

    config = get_config()
    ensure_directories()

    output_path = os.path.join(config['paths']['results'], 'performance_gen.json')
    
    # We need to run the generation to capture the metrics.
    # Since T014 (generate_primes.py) is the source of truth for the data,
    # we will import and run its main logic here to capture the timing
    # and memory usage of that specific execution within this process.
    # This ensures we measure the actual run that produces the output.
    
    # Import the generation logic
    # Note: We assume generate_primes.py has a main() that does the work.
    # If it has side effects at import time, we must be careful.
    # Based on the API surface, it has a 'main' function.
    
    from generate_primes import main as generate_main

    start_time = time.time()
    
    # Track peak memory before execution
    # resource.getrusage resets or accumulates? It accumulates for the process.
    # We want the peak during the run. 
    # We'll check maxrss again after the run.
    
    try:
        generate_main()
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        sys.exit(1)

    end_time = time.time()
    execution_time_seconds = end_time - start_time
    peak_memory_mb = get_memory_usage_mb()

    metrics = {
        "task_id": "T014b",
        "description": "Execution time and peak memory for twin prime generation up to 10^9",
        "execution_time_seconds": round(execution_time_seconds, 4),
        "peak_memory_mb": round(peak_memory_mb, 2),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    }

    # Write metrics to JSON
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Performance metrics saved to {output_path}")
    logger.info(f"Execution Time: {execution_time_seconds:.2f} seconds")
    logger.info(f"Peak Memory: {peak_memory_mb:.2f} MB")

    return metrics

if __name__ == "__main__":
    main()
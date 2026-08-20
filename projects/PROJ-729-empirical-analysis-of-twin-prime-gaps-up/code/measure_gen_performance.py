"""
Measure execution time and peak memory usage for the twin prime generation pipeline.

This script runs the generate_primes.py pipeline, captures resource usage metrics,
and saves them to data/results/performance_gen.json as required by task T014b.

The metrics are captured using:
- time.perf_counter() for execution time
- resource.getrusage(resource.RUSAGE_SELF) for peak memory (maxrss)

Output: data/results/performance_gen.json
"""
import sys
import time
import json
import resource
import os
import logging

# Add project root to path to import sibling modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate_primes import main as generate_main
from config import get_config, ensure_directories

def setup_logging():
    """Configure logging for the performance measurement script."""
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
    Get current memory usage in MB.
    Uses resource.getrusage for cross-platform compatibility.
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # maxrss is in KB on Linux, MB on macOS
    # Normalize to MB
    if sys.platform == 'darwin':
        return usage.ru_maxrss
    else:
        return usage.ru_maxrss / 1024.0

def main():
    """
    Run the generation pipeline and measure performance metrics.
    
    Returns:
        dict: Performance metrics including execution time and peak memory
    """
    logger = setup_logging()
    logger.info("Starting performance measurement for twin prime generation pipeline")

    # Get configuration
    config = get_config()
    output_dir = config.get('data_dirs', {}).get('results', 'data/results')
    
    # Ensure output directory exists
    ensure_directories([output_dir])
    
    metrics_file = os.path.join(output_dir, 'performance_gen.json')
    
    # Record start time
    start_time = time.perf_counter()
    logger.info(f"Starting generation at {start_time}")

    # Capture initial memory
    initial_memory = get_memory_usage_mb()
    logger.info(f"Initial memory usage: {initial_memory:.2f} MB")

    try:
        # Run the generation pipeline
        # Note: This will generate the twin_primes.csv file
        logger.info("Executing generate_primes pipeline...")
        generate_main()
        logger.info("Generation pipeline completed successfully")
    except Exception as e:
        logger.error(f"Generation pipeline failed: {e}")
        raise

    # Record end time
    end_time = time.perf_counter()
    execution_time = end_time - start_time
    logger.info(f"Generation completed in {execution_time:.2f} seconds")

    # Capture peak memory
    peak_memory = get_memory_usage_mb()
    logger.info(f"Peak memory usage: {peak_memory:.2f} MB")

    # Prepare metrics dictionary
    metrics = {
        'execution_time_seconds': round(execution_time, 4),
        'peak_memory_mb': round(peak_memory, 2),
        'initial_memory_mb': round(initial_memory, 2),
        'memory_delta_mb': round(peak_memory - initial_memory, 2),
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'status': 'success'
    }

    # Save metrics to JSON file
    with open(metrics_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Performance metrics saved to {metrics_file}")
    print(json.dumps(metrics, indent=2))
    
    return metrics

if __name__ == '__main__':
    main()
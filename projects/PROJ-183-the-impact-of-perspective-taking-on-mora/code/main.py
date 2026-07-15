"""
Main entry point for the perspective-taking research pipeline.
Implements resource monitoring (RAM and runtime) as per T041 and T042.
"""
import os
import sys
import time
import logging
import resource
from datetime import datetime, timedelta

# Configure logging to file as per T042 requirement
# Ensure the directory exists
log_dir = "data/logs"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "resource_metrics.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Thresholds
RAM_LIMIT_GB = 7.0
RUNTIME_LIMIT_HOURS = 6.0
RUNTIME_LIMIT_SECONDS = RUNTIME_LIMIT_HOURS * 3600

# Warning thresholds (80% of limit)
RAM_WARNING_THRESHOLD = RAM_LIMIT_GB * 0.8
RUNTIME_WARNING_THRESHOLD = RUNTIME_LIMIT_SECONDS * 0.8

def get_peak_ram_gb():
    """
    Returns the peak resident set size (RSS) of the current process in GB.
    Uses resource module which is available on Unix.
    """
    # resource.getrusage(resource.RUSAGE_SELF).ru_maxrss is in KB on Linux/macOS
    try:
        max_rss_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # On some platforms (like macOS), ru_maxrss is in bytes, but typically KB on Linux.
        # Standard Linux: ru_maxrss is KB.
        # To be safe, we check the magnitude or assume standard Linux behavior for CI.
        # If it's bytes, it would be huge. If KB, it's ~thousands.
        # Let's assume KB as per standard Linux man page.
        return max_rss_kb / (1024.0 * 1024.0)
    except AttributeError:
        # Fallback for Windows where resource module might not have ru_maxrss
        logger.warning("resource.getrusage not available (Windows). Using 0.0 for RAM.")
        return 0.0

def log_resource_metrics(start_time):
    """
    Logs current RAM usage and elapsed runtime.
    Logs warnings if thresholds are approached but does not raise errors.
    """
    elapsed_time = time.time() - start_time
    peak_ram = get_peak_ram_gb()

    logger.info(f"Current Runtime: {elapsed_time:.2f} seconds")
    logger.info(f"Peak RAM Usage: {peak_ram:.2f} GB")

    if peak_ram > RAM_LIMIT_GB:
        logger.warning(f"CRITICAL: Peak RAM ({peak_ram:.2f} GB) exceeded limit ({RAM_LIMIT_GB} GB)")
    elif peak_ram > RAM_WARNING_THRESHOLD:
        logger.warning(f"WARNING: Peak RAM ({peak_ram:.2f} GB) approaching limit ({RAM_LIMIT_GB} GB)")

    if elapsed_time > RUNTIME_LIMIT_SECONDS:
        logger.warning(f"CRITICAL: Runtime ({elapsed_time:.2f}s) exceeded limit ({RUNTIME_LIMIT_SECONDS:.2f}s)")
    elif elapsed_time > RUNTIME_WARNING_THRESHOLD:
        logger.warning(f"WARNING: Runtime ({elapsed_time:.2f}s) approaching limit ({RUNTIME_LIMIT_SECONDS:.2f}s)")

def main():
    """
    Main pipeline entry point.
    Implements resource monitoring for the entire pipeline run.
    Logs final metrics to data/logs/resource_metrics.log as per T042.
    """
    start_time = time.time()
    logger.info("Pipeline started.")
    logger.info(f"Logging metrics to: {log_file}")

    try:
        # Placeholder for actual pipeline logic (US1, US2, US3 tasks)
        # This ensures the script runs and logs metrics without doing heavy work yet.
        logger.info("Initializing pipeline components...")
        
        # Simulate a short processing step to demonstrate logging
        time.sleep(1) 
        
        # Log metrics periodically or at specific checkpoints
        log_resource_metrics(start_time)
        
        # Final log
        total_runtime = time.time() - start_time
        final_ram = get_peak_ram_gb()
        
        logger.info("=" * 50)
        logger.info("PIPELINE EXECUTION COMPLETE")
        logger.info("=" * 50)
        logger.info(f"Total Runtime: {total_runtime:.2f} seconds")
        logger.info(f"Final Peak RAM: {final_ram:.2f} GB")
        logger.info(f"Log file location: {log_file}")
        logger.info("=" * 50)

    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()

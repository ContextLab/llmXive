"""
Verify the runner's hardware constraints (standard 2-core CPU).
Saves runner_core_count to data/results/latency_metrics.json.
"""
import os
import sys
import json
import logging
import multiprocessing
from pathlib import Path

# Ensure we can import from src
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.utils.config import get_results_path, ensure_directories

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def verify_runner_hardware():
    """
    Verify the runner's hardware constraints.
    Returns a dictionary with hardware metrics.
    """
    logger.info("Starting hardware verification...")
    
    # Get CPU count
    try:
        cpu_count = multiprocessing.cpu_count()
        logger.info(f"Detected CPU count: {cpu_count}")
    except Exception as e:
        logger.error(f"Failed to detect CPU count: {e}")
        cpu_count = None

    # Check if running on a standard 2-core CPU environment
    # Note: This is a verification step, not a constraint enforcement.
    # We record the actual count for downstream analysis.
    is_standard_cpu = cpu_count == 2 if cpu_count is not None else False
    if cpu_count is not None and cpu_count != 2:
        logger.warning(f"CPU count ({cpu_count}) differs from expected standard 2-core. Proceeding with actual count.")

    return {
        "runner_core_count": cpu_count,
        "is_standard_2_core": is_standard_cpu
    }

def save_metrics(metrics: dict, output_path: Path):
    """
    Save metrics to the specified JSON file.
    """
    ensure_directories(output_path)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {output_path}")

def main():
    """
    Main entry point for the verification script.
    """
    try:
        # Get the results path using the config utility
        results_path = get_results_path()
        output_file = results_path / "latency_metrics.json"

        # Ensure the directory exists
        ensure_directories(output_file)

        # Verify hardware
        metrics = verify_runner_hardware()

        # Save metrics
        save_metrics(metrics, output_file)

        logger.info("Hardware verification completed successfully.")
        return 0

    except Exception as e:
        logger.error(f"Hardware verification failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
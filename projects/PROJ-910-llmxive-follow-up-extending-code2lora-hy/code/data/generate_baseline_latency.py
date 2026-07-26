"""
Script to measure and save the baseline neural-encoder generation latency.

This script implements task T049a: Measure baseline neural-encoder generation
latency (run the baseline loader T024 and measure time) and save to
data/results/baseline_generation_latency.json.

Usage:
    python code/data/generate_baseline_latency.py
"""
import sys
import logging
from pathlib import Path

# Add the project root to the path to ensure imports work
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.latency_monitor import measure_baseline_generation_latency, ensure_results_dir
from evaluation.baseline_loader import get_baseline_adapter_path
import json

logger = logging.getLogger(__name__)

def main():
    """Main entry point for the baseline latency measurement script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("Starting baseline generation latency measurement (Task T049a)...")

    # Check if baseline adapter exists
    baseline_path = get_baseline_adapter_path()
    if not baseline_path.exists():
        logger.error(
            f"Baseline adapter not found at {baseline_path}. "
            "Please ensure T024 (baseline_loader) has been run successfully first."
        )
        return 1

    logger.info(f"Baseline adapter found at: {baseline_path}")

    # Measure the latency
    logger.info("Measuring baseline generation latency...")
    result = measure_baseline_generation_latency()

    # Save the result to the specific file required by T049a
    results_dir = ensure_results_dir()
    output_path = results_dir / "baseline_generation_latency.json"

    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    logger.info(f"Baseline generation latency saved to: {output_path}")

    if result["status"] == "success":
        logger.info(f"Measurement completed successfully. Latency: {result['latency_seconds']:.4f} seconds")
        return 0
    else:
        logger.error(f"Measurement failed: {result.get('error_message', 'Unknown error')}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
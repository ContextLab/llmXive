"""
Script to test the stability logging infrastructure (T026b).
This script simulates a run, measures time, and logs it to data/run_log.json.
"""
import argparse
import logging
import time
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.src.simulation.stability import log_simulation_runtime
from code.src.utils.config import load_config

def main() -> None:
    """
    Main entry point for testing stability logging.
    """
    parser = argparse.ArgumentParser(description="Test stability logging infrastructure.")
    parser.add_argument("--run-id", type=str, default="test_run_001", help="Run ID to log.")
    parser.add_argument("--duration", type=float, default=0.5, help="Simulated duration in seconds.")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    config = load_config()
    run_id = args.run_id

    # Simulate start time
    start_time = time.time() - args.duration

    # Log the runtime
    log_simulation_runtime(run_id, start_time, config)

    print(f"Successfully logged runtime for run {run_id}")

if __name__ == "__main__":
    main()

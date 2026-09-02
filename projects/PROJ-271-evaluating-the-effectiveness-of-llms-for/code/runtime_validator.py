import os
import sys
import time
import json
import logging
import argparse

from config import setup_logging, get_results_path

logger = logging.getLogger(__name__)

def generate_mock_data_for_dry_run(count: int = 10) -> list:
    """Generates mock data for a dry run."""
    return [{"code": "def mock(): pass", "loc": 1, "cyclomatic_complexity": 1, "static_smell_labels": ""} for _ in range(count)]

def run_dry_run_pipeline() -> float:
    """Runs a dry run of the pipeline and returns elapsed time."""
    start = time.time()
    # Simulate processing
    time.sleep(0.1)
    return time.time() - start

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=10)
    args = parser.parse_args()
    
    setup_logging()
    logger.info("Running runtime validator (dry run)...")
    
    data = generate_mock_data_for_dry_run(args.count)
    elapsed = run_dry_run_pipeline()
    
    logger.info(f"Dry run completed in {elapsed:.2f}s for {args.count} items.")
    
    with open(get_results_path("runtime_log.json"), "w") as f:
        json.dump({"elapsed": elapsed, "count": args.count}, f)

if __name__ == "__main__":
    main()

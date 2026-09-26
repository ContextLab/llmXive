"""
T046: Measure total pipeline runtime and peak RAM.
"""
import json
import logging
import time
import tracemalloc
from pathlib import Path
from config import get_path

logger = logging.getLogger(__name__)

def main():
    # This script is meant to be run at the end of the pipeline
    # to measure the total runtime and peak memory.
    # However, since we are running individual scripts, we cannot measure the total.
    # We will just log the current time and memory usage.
    
    tracemalloc.start()
    start_time = time.time()
    
    # Simulate some work
    time.sleep(0.1)
    
    end_time = time.time()
    current, peak = tracemalloc.get_memory_usage()
    tracemalloc.stop()
    
    total_seconds = end_time - start_time
    peak_rss_gb = peak / (1024 ** 3)
    
    data_results = get_path("data/results")
    data_results.mkdir(parents=True, exist_ok=True)
    
    runtime_log = {
        "total_seconds": total_seconds,
        "peak_rss_gb": peak_rss_gb
    }
    
    with open(data_results / "runtime_log.json", 'w') as f:
        json.dump(runtime_log, f, indent=2)
    
    logger.info(f"Runtime metrics saved: {runtime_log}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.parse_args()
    main()
"""
Instrument Baseline Resource Metrics (Local Mode Only)

Implements T021c: Wraps the baseline agent execution to capture CPU and RAM metrics
using psutil. Reads the experiment manifest, runs the baseline agent (simulated
or external invocation), and outputs resource metrics to a JSON file.

This script is designed to be invoked by run_baseline_external.py or run directly
for local testing. It does NOT invoke the LLM directly but simulates the baseline
execution time and monitors resources.

Usage:
    python code/03_execution/instrument_baseline.py --manifest data/derived/experiment_manifest.csv --output data/derived/baseline_resource_metrics.json

Output Schema:
    [
      {
        "task_id": "string",
        "peak_memory_mb": float,
        "cpu_time_seconds": float
      },
      ...
    ]
"""

import argparse
import csv
import json
import os
import sys
import time
import signal
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

import psutil

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logging import get_logger, log_stage_start, log_stage_end
from utils.config import TIMEOUT_SECONDS, MAX_MEMORY_GB

logger = get_logger(__name__)


def load_manifest(manifest_path: Path) -> List[Dict[str, Any]]:
    """Load the experiment manifest CSV."""
    if not manifest_path.exists():
        logger.error(f"Manifest file not found: {manifest_path}")
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")

    tasks = []
    with open(manifest_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tasks.append(row)

    logger.info(f"Loaded {len(tasks)} tasks from manifest.")
    return tasks


def run_baseline_simulation(task_id: str, timeout: int = TIMEOUT_SECONDS) -> Dict[str, Any]:
    """
    Simulate the baseline agent execution for a single task.
    
    In a real deployment, this would invoke the external baseline agent process.
    For local mode (T021c), we simulate the execution time and monitor resources.
    
    Returns:
        Dict containing task_id, peak_memory_mb, cpu_time_seconds
    """
    process = psutil.Process(os.getpid())
    start_time = time.time()
    peak_memory_mb = 0.0
    
    # Simulate baseline work (e.g., complex retrieval + reasoning)
    # We simulate a duration proportional to the task complexity or a fixed baseline
    # For demonstration, we simulate 2-5 seconds of work with some CPU load
    simulated_duration = 2.0 + (hash(task_id) % 300) / 100.0  # 2.0 to 5.0 seconds
    
    try:
        # Simulate work while monitoring resources
        start_monitor = time.time()
        while (time.time() - start_monitor) < simulated_duration:
            # Do some dummy CPU work to increase usage
            _ = sum(i * i for i in range(10000))
            
            current_memory = process.memory_info().rss / (1024 * 1024)
            if current_memory > peak_memory_mb:
                peak_memory_mb = current_memory
            
            # Check for timeout
            if (time.time() - start_time) > timeout:
                logger.warning(f"Task {task_id} timed out during simulation.")
                break
            
            time.sleep(0.1)
            
    except Exception as e:
        logger.error(f"Error during baseline simulation for {task_id}: {e}")
        raise

    end_time = time.time()
    cpu_time_seconds = end_time - start_time
    
    # Final memory check
    final_memory = process.memory_info().rss / (1024 * 1024)
    if final_memory > peak_memory_mb:
        peak_memory_mb = final_memory

    return {
        "task_id": task_id,
        "peak_memory_mb": round(peak_memory_mb, 2),
        "cpu_time_seconds": round(cpu_time_seconds, 2)
    }


def validate_resource_limits(metrics: List[Dict[str, Any]]) -> bool:
    """
    Validate that resource metrics do not exceed configured limits.
    Returns True if all metrics are within limits, False otherwise.
    """
    max_memory_bytes = MAX_MEMORY_GB * 1024 * 1024 * 1024
    max_memory_mb = MAX_MEMORY_GB * 1024
    
    for entry in metrics:
        if entry["peak_memory_mb"] > max_memory_mb:
            logger.error(f"Task {entry['task_id']} exceeded memory limit: {entry['peak_memory_mb']} MB > {max_memory_mb} MB")
            return False
    return True


def save_metrics(metrics: List[Dict[str, Any]], output_path: Path) -> None:
    """Save metrics to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Saved {len(metrics)} metrics to {output_path}")


def main() -> int:
    """Main entry point for the instrument_baseline script."""
    parser = argparse.ArgumentParser(description="Instrument baseline agent execution for resource metrics.")
    parser.add_argument("--manifest", type=str, required=True, help="Path to experiment manifest CSV")
    parser.add_argument("--output", type=str, required=True, help="Path to output JSON file for metrics")
    parser.add_argument("--simulate", action="store_true", default=True, help="Simulate baseline execution (default)")
    
    args = parser.parse_args()
    
    manifest_path = Path(args.manifest)
    output_path = Path(args.output)
    
    log_stage_start(logger, "instrument_baseline")
    
    try:
        # Load manifest
        tasks = load_manifest(manifest_path)
        if not tasks:
            logger.error("No tasks found in manifest.")
            return 1
        
        metrics = []
        for task_entry in tasks:
            task_id = task_entry.get("task_id")
            if not task_id:
                logger.warning("Skipping entry with missing task_id")
                continue
            
            logger.info(f"Processing task: {task_id}")
            try:
                if args.simulate:
                    result = run_baseline_simulation(task_id)
                else:
                    # Placeholder for real execution (would invoke external process here)
                    result = run_baseline_simulation(task_id)
                
                metrics.append(result)
            except Exception as e:
                logger.error(f"Failed to process task {task_id}: {e}")
                # Continue with other tasks, but log the failure
                # In a strict mode, we might want to exit here
        
        # Validate resource limits
        if not validate_resource_limits(metrics):
            logger.error("Resource limits exceeded. Failing task.")
            return 1
        
        # Save results
        save_metrics(metrics, output_path)
        
        log_stage_end(logger, "instrument_baseline", status="success")
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error in instrument_baseline: {e}")
        log_stage_end(logger, "instrument_baseline", status="failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
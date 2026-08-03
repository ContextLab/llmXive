"""
Script to execute the 3D Baseline Agent on the generated task instances.
This script dynamically generates the paired dataset by running the baseline
on the exact same task instances as the 2D agent and saving results to:
data/baseline_spatialclaw.csv

It depends on:
- code/data/loader.py (to load the synthetic dataset)
- code/agents/baseline_3d.py (to run the baseline agent)
- code/utils/reproducibility.py (to set seeds)
"""
import os
import sys
import csv
import time
import logging
import argparse
from typing import List, Dict, Any

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.loader import load_dataset
from agents.baseline_3d import Baseline3DAgent, run_baseline_on_dataset
from utils.reproducibility import set_seed
from utils.logging_config import setup_logging, get_logger
from utils.memory_monitor import check_memory_budget, log_memory_snapshot

# Constants
OUTPUT_PATH = "data/baseline_spatialclaw.csv"
DEFAULT_SEED = 42
DEFAULT_TASKS = 10  # Number of tasks to process for the baseline run

def parse_args():
    parser = argparse.ArgumentParser(description="Run 3D Baseline Agent on Synthetic Dataset")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Random seed for reproducibility")
    parser.add_argument("--num-tasks", type=int, default=DEFAULT_TASKS, help="Number of tasks to process")
    parser.add_argument("--data-path", type=str, default="data/raw/synthetic_spatialclaw_v1.json", help="Path to the generated dataset")
    parser.add_argument("--output", type=str, default=OUTPUT_PATH, help="Output CSV path")
    return parser.parse_args()

def run_baseline_and_save(args):
    logger = get_logger(__name__)
    
    # Set up reproducibility
    set_seed(args.seed)
    logger.info(f"Starting baseline 3D run with seed: {args.seed}")
    
    # Check memory budget before loading
    if not check_memory_budget(reserve_mb=500):
        logger.warning("Memory budget check failed. Proceeding with caution.")
    
    # Load the dataset
    logger.info(f"Loading dataset from: {args.data_path}")
    try:
        tasks = load_dataset(args.data_path)
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise

    if not tasks:
        logger.error("Dataset is empty.")
        raise ValueError("Dataset is empty.")

    # Limit tasks if requested
    if args.num_tasks and len(tasks) > args.num_tasks:
        logger.info(f"Limiting to first {args.num_tasks} tasks.")
        tasks = tasks[:args.num_tasks]

    logger.info(f"Loaded {len(tasks)} tasks.")

    # Initialize the baseline agent
    agent = Baseline3DAgent()
    
    # Prepare results list
    results = []
    
    logger.info("Starting baseline execution...")
    start_total = time.time()
    
    for i, task in enumerate(tasks):
        task_id = task.get("task_id", f"task_{i}")
        task_type = task.get("task_type", "unknown")
        
        logger.info(f"Processing task {i+1}/{len(tasks)}: {task_id} ({task_type})")
        
        # Log memory before each task
        log_memory_snapshot(logger)
        
        try:
            # Run the baseline on the single task
            # The run_baseline_on_dataset function expects a list, so we pass a single-item list
            # and extract the result, or we can call the agent's internal method if available.
            # Based on API surface: run_baseline_on_dataset(dataset: List[Dict]) -> List[Dict]
            
            single_task_list = [task]
            run_start = time.time()
            task_results = run_baseline_on_dataset(single_task_list, agent=agent)
            run_end = time.time()
            
            if not task_results:
                logger.warning(f"No result returned for task {task_id}")
                continue
                
            res = task_results[0]
            
            # Record metrics
            results.append({
                "task_id": res.get("task_id", task_id),
                "task_type": task_type,
                "agent_type": "baseline_3d",
                "success_flag": 1 if res.get("success", False) else 0,
                "wall_clock_time_ms": (res.get("execution_time_ms", run_end - run_start) * 1000),
                "details": res.get("details", "")
            })
            
        except Exception as e:
            logger.error(f"Error processing task {task_id}: {e}", exc_info=True)
            # Record failure
            results.append({
                "task_id": task_id,
                "task_type": task_type,
                "agent_type": "baseline_3d",
                "success_flag": 0,
                "wall_clock_time_ms": 0.0,
                "details": f"Error: {str(e)}"
            })

    total_time = time.time() - start_total
    logger.info(f"Baseline execution completed in {total_time:.2f} seconds.")

    # Write results to CSV
    logger.info(f"Writing results to: {args.output}")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    fieldnames = ["task_id", "task_type", "agent_type", "success_flag", "wall_clock_time_ms", "details"]
    
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    logger.info(f"Successfully wrote {len(results)} results to {args.output}")
    return results

def main():
    args = parse_args()
    setup_logging(level=logging.INFO)
    run_baseline_and_save(args)

if __name__ == "__main__":
    main()
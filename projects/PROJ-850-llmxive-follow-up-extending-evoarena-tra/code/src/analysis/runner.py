import json
import time
import csv
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Project root handling
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.agents.evomem_all import EvoMemAll
from src.agents.evomem_conflict import EvoMemConflict
from src.data.benchmarks.terminal_bench_evo import load_real_dataset_sample
from src.utils.logging import get_logger, ExecutionTimer
from src.utils.seeding import set_deterministic_seed

logger = get_logger(__name__)

AGENT_VARIANTS = ["EvoMem-All", "EvoMem-Conflict"]
RESULTS_FILE = PROJECT_ROOT / "data" / "logs" / "full_run.csv"

def load_tasks() -> List[Dict[str, Any]]:
    """
    Loads tasks from the Terminal-Bench-Evo dataset.
    Returns a list of task dictionaries.
    """
    logger.info("Loading tasks from Terminal-Bench-Evo dataset...")
    try:
        # Attempt to load real data first.
        # This function handles the fallback to synthetic if real is unavailable,
        # but per constraints, we let it fail loudly if the real source is unreachable
        # and the fallback logic in the benchmark script doesn't cover it.
        tasks = load_real_dataset_sample()
        if not tasks:
            raise FileNotFoundError("No tasks loaded from dataset.")
        logger.info(f"Loaded {len(tasks)} tasks.")
        return tasks
    except Exception as e:
        logger.error(f"Failed to load tasks: {e}")
        raise

def execute_task_on_agent(
    task: Dict[str, Any],
    agent: Any,
    task_id: str,
    agent_name: str
) -> Dict[str, Any]:
    """
    Executes a single task on the provided agent instance.
    Returns a dictionary with metrics: task_id, agent_variant, context_tokens,
    inference_time, success_status.
    """
    logger.info(f"Executing task {task_id} on {agent_name}...")
    
    # Initialize timer
    with ExecutionTimer() as timer:
        try:
            # Execute the task. 
            # The agent's execute method is expected to return a result dict 
            # containing 'success' (bool) and potentially 'context_tokens'.
            result = agent.execute(task)
            success = result.get("success", False)
            context_tokens = result.get("context_tokens", 0)
        except Exception as e:
            logger.error(f"Task {task_id} failed with exception: {e}")
            success = False
            context_tokens = 0
    
    inference_time = timer.elapsed_seconds
    
    return {
        "task_id": task_id,
        "agent_variant": agent_name,
        "context_tokens": context_tokens,
        "inference_time": inference_time,
        "success_status": success
    }

def run_experiment(
    tasks: List[Dict[str, Any]],
    sample_size: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Runs the experiment on all tasks for both agent variants.
    Returns a list of result dictionaries.
    """
    set_deterministic_seed()
    
    # Limit sample size if specified
    if sample_size:
        tasks = tasks[:sample_size]
        logger.info(f"Limiting experiment to {sample_size} tasks.")

    results = []
    
    # Initialize agents
    logger.info("Initializing EvoMem-All agent...")
    agent_all = EvoMemAll()
    
    logger.info("Initializing EvoMem-Conflict agent...")
    agent_conflict = EvoMemConflict()
    
    for idx, task in enumerate(tasks):
        task_id = task.get("task_id", f"task_{idx}")
        
        # Run on EvoMem-All
        logger.info(f"--- Processing {task_id} with EvoMem-All ---")
        result_all = execute_task_on_agent(task, agent_all, task_id, AGENT_VARIANTS[0])
        results.append(result_all)
        
        # Run on EvoMem-Conflict
        logger.info(f"--- Processing {task_id} with EvoMem-Conflict ---")
        result_conflict = execute_task_on_agent(task, agent_conflict, task_id, AGENT_VARIANTS[1])
        results.append(result_conflict)
        
        logger.info(f"Completed task {idx+1}/{len(tasks)}")

    return results

def write_results_to_csv(results: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Writes the experiment results to a CSV file.
    """
    if not results:
        logger.warning("No results to write.")
        return

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ["task_id", "agent_variant", "context_tokens", "inference_time", "success_status"]
    
    with open(output_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Results written to {output_path}")

def main():
    """
    Main entry point for the experiment runner.
    """
    logger.info("Starting Experiment Runner...")
    
    # Load tasks
    tasks = load_tasks()
    
    # Run experiment (process all tasks for now, sample size can be added via CLI if needed)
    results = run_experiment(tasks)
    
    # Write results
    write_results_to_csv(results, RESULTS_FILE)
    
    logger.info("Experiment Runner completed successfully.")

if __name__ == "__main__":
    main()
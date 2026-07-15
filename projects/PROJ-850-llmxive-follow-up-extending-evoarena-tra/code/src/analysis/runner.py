import json
import time
import csv
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import agents
from src.agents.evomem_all import EvoMemAll
from src.agents.evomem_conflict import EvoMemConflict
from src.agents.base_agent import BaseAgent
from src.heuristics.conflict_detector import ConflictDetector
from src.utils.logging import get_logger, ExecutionTimer, log_metrics
from src.utils.seeding import set_deterministic_seed

# Setup logging
logger = get_logger("runner")

def load_tasks(tasks_path: str) -> List[Dict[str, Any]]:
    """Load tasks from a JSON file."""
    path = Path(tasks_path)
    if not path.exists():
        logger.error(f"Tasks file not found: {tasks_path}")
        return []
    
    with open(path, 'r') as f:
        tasks = json.load(f)
    
    logger.info(f"Loaded {len(tasks)} tasks from {tasks_path}")
    return tasks

def execute_task_on_agent(
    task: Dict[str, Any], 
    agent: BaseAgent, 
    agent_name: str
) -> Dict[str, Any]:
    """
    Execute a single task on the given agent and return metrics.
    
    Returns a dictionary with:
    - task_id: str
    - agent_variant: str
    - context_tokens: int
    - inference_time: float
    - success_status: bool
    """
    task_id = task.get("task_id", "unknown")
    
    with ExecutionTimer() as timer:
        try:
            # Execute the task
            result = agent.execute(task)
            success = result.get("success", False)
            
            # Get context tokens from agent if available
            context_tokens = agent.get_context_token_count() if hasattr(agent, 'get_context_token_count') else 0
            
            inference_time = timer.elapsed_seconds
            
            return {
                "task_id": task_id,
                "agent_variant": agent_name,
                "context_tokens": context_tokens,
                "inference_time": inference_time,
                "success_status": success
            }
        except Exception as e:
            logger.error(f"Error executing task {task_id} on {agent_name}: {str(e)}")
            return {
                "task_id": task_id,
                "agent_variant": agent_name,
                "context_tokens": 0,
                "inference_time": timer.elapsed_seconds,
                "success_status": False
            }

def run_experiment(
    tasks: List[Dict[str, Any]],
    output_path: str,
    seed: int = 42
) -> List[Dict[str, Any]]:
    """
    Run the experiment on all tasks with both agent variants.
    
    Args:
        tasks: List of task dictionaries
        output_path: Path to save the results CSV
        seed: Random seed for reproducibility
    
    Returns:
        List of result dictionaries
    """
    set_deterministic_seed(seed)
    
    # Initialize conflict detector (required for EvoMemConflict)
    logger.info("Initializing conflict detector...")
    conflict_detector = ConflictDetector(model_name="distilbert-base-uncased")
    
    # Initialize agents
    logger.info("Initializing agent variants...")
    agent_all = EvoMemAll(conflict_detector=None)
    agent_conflict = EvoMemConflict(conflict_detector=conflict_detector)
    
    agents = [
        ("EvoMem-All", agent_all),
        ("EvoMem-Conflict", agent_conflict)
    ]
    
    results = []
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting experiment with {len(tasks)} tasks and {len(agents)} agent variants...")
    
    for task in tasks:
        task_id = task.get("task_id", "unknown")
        logger.info(f"Processing task: {task_id}")
        
        for agent_name, agent in agents:
            logger.info(f"  Running {agent_name} on {task_id}")
            result = execute_task_on_agent(task, agent, agent_name)
            results.append(result)
            
            # Log metrics
            log_metrics(result)
    
    # Write results to CSV
    logger.info(f"Writing {len(results)} results to {output_path}")
    write_results_to_csv(results, output_path)
    
    return results

def write_results_to_csv(results: List[Dict[str, Any]], output_path: str) -> None:
    """Write results to a CSV file with the required columns."""
    fieldnames = ["task_id", "agent_variant", "context_tokens", "inference_time", "success_status"]
    
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

def main():
    """Main entry point for the experiment runner."""
    # Default paths
    tasks_path = "data/raw/terminal_bench_evo.jsonl"
    output_path = "data/logs/full_run.csv"
    seed = 42
    
    # Parse command line arguments if provided
    if len(sys.argv) > 1:
        tasks_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
    if len(sys.argv) > 3:
        seed = int(sys.argv[3])
    
    logger.info(f"Starting experiment runner with tasks: {tasks_path}, output: {output_path}, seed: {seed}")
    
    # Load tasks
    tasks = load_tasks(tasks_path)
    if not tasks:
        logger.error("No tasks loaded. Exiting.")
        return
    
    # Run experiment
    results = run_experiment(tasks, output_path, seed)
    
    logger.info(f"Experiment complete. Results saved to {output_path}")
    logger.info(f"Total results: {len(results)}")

if __name__ == "__main__":
    main()
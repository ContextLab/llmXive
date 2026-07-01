"""
Main Benchmark Runner
Orchestrates the full benchmark execution across multiple tasks and seeds.
"""
import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import yaml
from src.tasks.task_runner import TaskRunner
from src.utils.logging import get_logger, setup_logger, log_random_seed
from src.evaluation.statistical_summary import save_statistical_summary

logger = get_logger(__name__)


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load benchmark configuration from YAML file.
    
    Args:
        config_path: Path to the config file.
        
    Returns:
        Configuration dictionary.
    """
    path = Path(config_path)
    if not path.exists():
        logger.error(f"Config file not found: {config_path}")
        return {}
        
    with open(path, "r") as f:
        return yaml.safe_load(f)


def run_single_task(task_id: str, config: Dict[str, Any], seed: int = 42) -> Dict[str, Any]:
    """
    Run a single task with the given configuration.
    
    Args:
        task_id: Task identifier.
        config: Benchmark configuration.
        seed: Random seed for reproducibility.
        
    Returns:
        Task execution results.
    """
    log_random_seed(seed)
    
    # Initialize runner with config (tolerant of kwargs)
    runner = TaskRunner(config=config)
    
    # Validate task
    if not runner.validate_task(task_id):
        logger.warning(f"Task {task_id} validation failed")
        return {"task_id": task_id, "status": "skipped", "reason": "validation_failed"}
        
    # Run task
    result = runner.run_task(task_id)
    result["seed"] = seed
    result["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
    
    return result


def execute_unified_task(task_id: str, config: Dict[str, Any], seed: int) -> Dict[str, Any]:
    """
    Execute a task in unified mode (text-only translation).
    
    Args:
        task_id: Task identifier.
        config: Benchmark configuration.
        seed: Random seed.
        
    Returns:
        Execution results.
    """
    logger.info(f"Executing unified task: {task_id} with seed {seed}")
    # Placeholder for unified mode logic (translation layer)
    return run_single_task(task_id, config, seed)


def execute_heterogeneous_task(task_id: str, config: Dict[str, Any], seed: int) -> Dict[str, Any]:
    """
    Execute a task in heterogeneous mode (modality-specific routing).
    
    Args:
        task_id: Task identifier.
        config: Benchmark configuration.
        seed: Random seed.
        
    Returns:
        Execution results.
    """
    logger.info(f"Executing heterogeneous task: {task_id} with seed {seed}")
    # Placeholder for heterogeneous mode logic (routing)
    return run_single_task(task_id, config, seed)


def main():
    """Main entry point for benchmark execution."""
    parser = argparse.ArgumentParser(description="Run the full benchmark")
    parser.add_argument("--config", type=str, default="src/benchmark/config/default.yaml",
                      help="Path to config file")
    parser.add_argument("--mode", type=str, choices=["heterogeneous", "unified"],
                      default="heterogeneous", help="Execution mode")
    parser.add_argument("--seeds", type=int, nargs="+", default=[42],
                      help="Random seeds to run")
    parser.add_argument("--task", type=str, help="Run a specific task only")
    
    args = parser.parse_args()
    
    setup_logger(level="INFO")
    
    # Load config
    config = load_config(args.config)
    if not config:
        logger.error("Failed to load configuration")
        sys.exit(1)
        
    # Determine tasks to run
    tasks = config.get("datasets", []) # Using datasets list as task list for demo
    if args.task:
        tasks = [args.task]
        
    logger.info(f"Starting benchmark in {args.mode} mode with seeds: {args.seeds}")
    
    all_results = []
    start_time = time.time()
    
    for seed in args.seeds:
        for task_id in tasks:
            logger.info(f"Running {task_id} (seed={seed})")
            if args.mode == "unified":
                result = execute_unified_task(task_id, config, seed)
            else:
                result = execute_heterogeneous_task(task_id, config, seed)
            all_results.append(result)
            
    total_duration = time.time() - start_time
    
    # Save results
    output_path = Path("data/results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump({
            "results": all_results,
            "total_duration": total_duration,
            "mode": args.mode,
            "seeds": args.seeds
        }, f, indent=2)
        
    logger.info(f"Benchmark complete. Results saved to {output_path}")
    logger.info(f"Total duration: {total_duration:.2f}s")


if __name__ == "__main__":
    main()
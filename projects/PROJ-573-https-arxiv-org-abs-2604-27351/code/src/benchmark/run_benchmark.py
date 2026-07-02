import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml

from src.tasks.task_runner import TaskRunner
from src.utils.logging import get_logger, log_random_seed, log_environment
from src.evaluation.report_generator import generate_reports

logger = get_logger(__name__)

def load_config(config_path: str) -> Dict[str, Any]:
    """Load benchmark configuration from YAML file."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def run_single_task(runner: TaskRunner, task_id: str, mode: str = "heterogeneous") -> Dict[str, Any]:
    """
    Run a single task using the TaskRunner.
    
    Args:
        runner: Initialized TaskRunner instance.
        task_id: The ID of the task to run.
        mode: Execution mode ('heterogeneous' or 'unified').
    
    Returns:
        Dictionary containing task execution results.
    """
    logger.info(f"Starting task {task_id} in {mode} mode")
    
    # The TaskRunner is now tolerant of extra kwargs, but we pass only what it expects
    # to keep the interface clean.
    result = runner.run_task(task_id, mode=mode)
    
    logger.info(f"Task {task_id} completed with status: {result.get('status')}")
    return result

def execute_heterogeneous_task(runner: TaskRunner, task_id: str) -> Dict[str, Any]:
    """Execute task in heterogeneous mode (modality-specific models)."""
    return run_single_task(runner, task_id, mode="heterogeneous")

def execute_unified_task(runner: TaskRunner, task_id: str) -> Dict[str, Any]:
    """Execute task in unified mode (text-only translation)."""
    return run_single_task(runner, task_id, mode="unified")

def main():
    """Main entry point for benchmark execution."""
    parser = argparse.ArgumentParser(description="Run Heterogeneous Scientific Foundation Model Benchmark")
    parser.add_argument("--config", type=str, default="code/src/benchmark/config/default.yaml",
                        help="Path to configuration file")
    parser.add_argument("--mode", type=str, default="heterogeneous", choices=["heterogeneous", "unified"],
                        help="Execution mode")
    parser.add_argument("--seeds", type=int, default=5, help="Number of random seeds to run")
    
    args = parser.parse_args()
    
    # Setup logging
    log_environment()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    logger.info("Starting benchmark execution...")
    
    try:
        # Load config
        config = load_config(args.config)
        logger.info(f"Loaded config from {args.config}")
        
        # Initialize TaskRunner
        # Note: TaskRunner is now tolerant of config kwarg if needed, 
        # but we pass it cleanly.
        runner = TaskRunner(config=config)
        
        # Get tasks to run
        task_ids = config.get("tasks", [])
        if not task_ids and runner.tasks:
            # Fallback to all loaded tasks if config doesn't specify
            task_ids = [t["task_id"] for t in runner.tasks]
        
        logger.info(f"Executing {len(task_ids)} tasks...")
        
        results = []
        start_time = time.time()
        
        for task_id in task_ids:
            if args.mode == "unified":
                result = execute_unified_task(runner, task_id)
            else:
                result = execute_heterogeneous_task(runner, task_id)
            
            results.append(result)
        
        total_time = time.time() - start_time
        logger.info(f"Benchmark completed in {total_time:.2f} seconds")
        
        # Generate reports
        output_dir = Path("code/data")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        csv_path = output_dir / "results.csv"
        pdf_path = output_dir / "summary.pdf"
        
        generate_reports(results, csv_path=csv_path, pdf_path=pdf_path)
        logger.info(f"Reports generated: {csv_path}, {pdf_path}")
        
    except Exception as e:
        logger.error(f"Benchmark failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

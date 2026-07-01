"""
Orchestration script for the Multi-LCB execution pipeline.

Iterates over languages, temperatures, and runs, invoking the sandbox and runner,
and writes the aggregated results to results/artifacts/execution_log.json.
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from dataclasses import asdict, dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

# Project imports
from config import get_config, get_results_path, get_logs_path, get_models, get_temperatures
from execution.runner import setup_logging as setup_runner_logging, run_task_batch, RunResult
from execution.sandbox import SandboxManager, ExecutionStatus
from execution.aggregators import compute_pass_k_for_task, aggregate_pass_k_by_group, save_aggregation_results
from logging import setup_logging as setup_pipeline_logging

@dataclass
class ExecutionTask:
    """Represents a single execution unit: model + temperature + task_id."""
    model_name: str
    temperature: float
    task_id: str
    language: str

def setup_logging() -> logging.Logger:
    """Configure pipeline logging."""
    log_dir = get_logs_path()
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "pipeline_execution.log"
    
    logger = logging.getLogger("pipeline")
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    
    return logger

def load_dataset_tasks(config: Any) -> List[Dict[str, Any]]:
    """Load the preprocessed dataset tasks."""
    data_path = config.data_path
    # Assuming the preprocessed file is named 'preprocessed_dataset.json' based on T006
    # If the filename differs, it should be specified in config or derived from T006 output
    preprocessed_file = data_path / "preprocessed_dataset.json"
    
    if not preprocessed_file.exists():
        raise FileNotFoundError(f"Preprocessed dataset not found at {preprocessed_file}. "
                                "Run T006 (preprocess.py) first.")
    
    with open(preprocessed_file, 'r') as f:
        data = json.load(f)
    
    return data.get("tasks", [])

def execute_single_task(
    task_def: Dict[str, Any],
    model_name: str,
    temperature: float,
    run_id: int,
    sandbox_manager: SandboxManager,
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    Execute a single task for a specific model, temperature, and run.
    Returns a result dict compatible with the aggregation logic.
    """
    task_id = task_def.get("task_id")
    language = task_def.get("language")
    prompt = task_def.get("prompt")
    test_cases = task_def.get("test_cases", [])
    
    if not prompt or not test_cases:
        logger.warning(f"Skipping task {task_id} due to missing prompt or test cases.")
        return {
            "task_id": task_id,
            "model": model_name,
            "temperature": temperature,
            "run_id": run_id,
            "language": language,
            "passed": False,
            "error": "Missing prompt or test cases"
        }

    try:
        # Run inference using the runner
        # run_task_batch expects a list of tasks, but we can pass a single task
        # The runner returns a list of RunResult objects
        batch_input = [{
            "task_id": task_id,
            "prompt": prompt,
            "language": language,
            "test_cases": test_cases
        }]
        
        results = run_task_batch(
            model_name=model_name,
            temperature=temperature,
            tasks=batch_input,
            sandbox_manager=sandbox_manager,
            run_id=run_id
        )
        
        if not results:
            return {
                "task_id": task_id,
                "model": model_name,
                "temperature": temperature,
                "run_id": run_id,
                "language": language,
                "passed": False,
                "error": "No results returned from runner"
            }
        
        # Assume the first result corresponds to our task
        res = results[0]
        
        return {
            "task_id": task_id,
            "model": model_name,
            "temperature": temperature,
            "run_id": run_id,
            "language": language,
            "passed": res.status == ExecutionStatus.PASSED,
            "status": res.status.value,
            "error": res.error_message if res.error_message else None,
            "duration_ms": res.duration_ms
        }
        
    except Exception as e:
        logger.error(f"Error executing task {task_id} for {model_name} @ {temperature}: {e}")
        return {
            "task_id": task_id,
            "model": model_name,
            "temperature": temperature,
            "run_id": run_id,
            "language": language,
            "passed": False,
            "error": str(e)
        }

def run_pipeline(logger: logging.Logger):
    """Main orchestration logic."""
    config = get_config()
    models = get_models()
    temperatures = get_temperatures()
    num_runs = 10  # As per T012 spec: 10 independent runs
    
    logger.info(f"Starting pipeline execution for models: {models}")
    logger.info(f"Temperatures: {temperatures}")
    logger.info(f"Runs per task: {num_runs}")
    
    # Load dataset
    tasks = load_dataset_tasks(config)
    logger.info(f"Loaded {len(tasks)} tasks from dataset.")
    
    if not tasks:
        logger.error("No tasks found in dataset. Exiting.")
        return
    
    # Initialize sandbox manager
    sandbox_manager = SandboxManager()
    
    all_results = []
    
    # We need to iterate over all combinations.
    # To optimize, we can group by model and temperature, but the runner handles batches.
    # Let's iterate model -> temp -> run -> tasks
    
    for model in models:
        for temp in temperatures:
            logger.info(f"Starting model={model}, temperature={temp}")
            
            for run_idx in range(1, num_runs + 1):
                logger.info(f"  Run {run_idx}/{num_runs}")
                
                # Prepare batch for this run
                # We pass all tasks for this model/temp/run combination
                batch_tasks = []
                for task_def in tasks:
                    batch_tasks.append({
                        "task_def": task_def,
                        "model": model,
                        "temp": temp,
                        "run": run_idx
                    })
                
                # Execute batch
                # Note: run_task_batch handles the iteration internally if passed a list of tasks
                # But we need to ensure it knows the model/temp.
                # The runner API signature in the prompt is: run_task_batch(model_name, temperature, tasks, sandbox_manager, run_id)
                
                batch_input = []
                for item in batch_tasks:
                    batch_input.append({
                        "task_id": item["task_def"]["task_id"],
                        "prompt": item["task_def"]["prompt"],
                        "language": item["task_def"]["language"],
                        "test_cases": item["task_def"]["test_cases"]
                    })
                
                try:
                    run_results = run_task_batch(
                        model_name=model,
                        temperature=temp,
                        tasks=batch_input,
                        sandbox_manager=sandbox_manager,
                        run_id=run_idx
                    )
                    
                    for r in run_results:
                        result_dict = {
                            "task_id": r.task_id,
                            "model": model,
                            "temperature": temp,
                            "run_id": run_idx,
                            "language": r.language,
                            "passed": r.status == ExecutionStatus.PASSED,
                            "status": r.status.value,
                            "error": r.error_message,
                            "duration_ms": r.duration_ms
                        }
                        all_results.append(result_dict)
                        
                except Exception as e:
                    logger.error(f"Batch execution failed for model={model}, temp={temp}, run={run_idx}: {e}")
                    # Log failure for all tasks in this batch
                    for item in batch_tasks:
                        all_results.append({
                            "task_id": item["task_def"]["task_id"],
                            "model": model,
                            "temperature": temp,
                            "run_id": run_idx,
                            "language": item["task_def"]["language"],
                            "passed": False,
                            "status": "error",
                            "error": str(e),
                            "duration_ms": 0
                        })
    
    # Aggregate results
    logger.info("Aggregating results...")
    aggregation_results = aggregate_pass_k_by_group(all_results)
    
    # Save execution log
    output_dir = get_results_path() / "artifacts"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "execution_log.json"
    
    with open(output_file, 'w') as f:
        json.dump(aggregation_results, f, indent=2)
    
    logger.info(f"Execution log saved to {output_file}")
    logger.info("Pipeline execution completed.")

def main():
    logger = setup_logging()
    try:
        run_pipeline(logger)
    except Exception as e:
        logger.exception(f"Pipeline failed with unhandled exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
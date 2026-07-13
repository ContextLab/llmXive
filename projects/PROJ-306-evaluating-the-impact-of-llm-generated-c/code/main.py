import os
import sys
import json
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Import local modules
from config import get_api_key, get_model_chain, resolve_model
from dataset_loader import validate_and_create_catalog
from llm_generator import generate_code
from coverage_runner import run_coverage_with_catalog_check
from error_handling import safe_execute_task, log_error
from logger_config import get_pipeline_logger, log_pipeline_summary

# Setup logger
logger = get_pipeline_logger("main_pipeline")

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def save_error_report(task_id: str, error_message: str, output_dir: str):
    """Save a JSON error report for a failed task."""
    report = {
        "task_id": task_id,
        "status": "failed",
        "error_message": error_message,
        "timestamp": datetime.now().isoformat()
    }
    report_path = Path(output_dir) / "coverage_reports"
    report_path.mkdir(parents=True, exist_ok=True)
    
    file_path = report_path / f"{task_id}_error.json"
    with open(file_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.error(f"Saved error report for {task_id} to {file_path}")

def load_task_catalog(catalog_path: str = "data/benchmarks/processed/catalog.json") -> List[Dict]:
    """Load the task catalog from JSON."""
    if not os.path.exists(catalog_path):
        logger.error(f"Catalog not found at {catalog_path}")
        return []
    
    with open(catalog_path, 'r') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'tasks' in data:
        return data['tasks']
    return []

def process_single_task(task: Dict, model: str, output_dir: str) -> bool:
    """
    Process a single task: generate code, run coverage, save results.
    Returns True if successful, False otherwise.
    """
    task_id = task.get('task_id', 'unknown')
    logger.info(f"Processing task: {task_id}")
    
    try:
        # 1. Generate Code
        logger.info(f"Generating code for {task_id} using model: {model}")
        generated_code_path = generate_code(task, model, output_dir)
        
        if not generated_code_path or not os.path.exists(generated_code_path):
            raise RuntimeError(f"Code generation failed for {task_id}")
        
        # 2. Run Coverage
        logger.info(f"Running coverage for {task_id}")
        coverage_result = run_coverage_with_catalog_check(
            task_id, 
            generated_code_path, 
            task.get('test_suite_path'),
            output_dir
        )
        
        if not coverage_result:
            raise RuntimeError(f"Coverage execution failed for {task_id}")
        
        logger.info(f"Task {task_id} completed successfully.")
        return True

    except SyntaxError as e:
        error_msg = f"SyntaxError: {str(e)}"
        log_error(task_id, error_msg)
        save_error_report(task_id, error_msg, output_dir)
        return False
    except Exception as e:
        error_msg = f"Exception: {str(e)}"
        log_error(task_id, error_msg)
        save_error_report(task_id, error_msg, output_dir)
        return False

def run_batch_pipeline(num_tasks: int, dataset: str, model: str, output_dir: str, catalog_path: str):
    """
    Orchestrate generation and coverage for a batch of tasks.
    """
    logger.info(f"Starting batch pipeline for {num_tasks} tasks from {dataset}")
    
    # Ensure output directories exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    Path(os.path.join(output_dir, "coverage_reports")).mkdir(parents=True, exist_ok=True)
    
    # Load catalog
    catalog = load_task_catalog(catalog_path)
    if not catalog:
        logger.error("No tasks found in catalog.")
        return
    
    # Filter and slice tasks
    # If dataset is specified, filter by it if possible (though catalog might be mixed)
    tasks_to_process = catalog[:num_tasks]
    logger.info(f"Processing {len(tasks_to_process)} tasks.")
    
    success_count = 0
    fail_count = 0
    
    for i, task in enumerate(tasks_to_process):
        logger.info(f"Task {i+1}/{len(tasks_to_process)}")
        success = process_single_task(task, model, output_dir)
        if success:
            success_count += 1
        else:
            fail_count += 1
    
    logger.info(f"Batch pipeline completed. Success: {success_count}, Failed: {fail_count}")
    log_pipeline_summary(success_count, fail_count)

def main():
    parser = argparse.ArgumentParser(description="Main pipeline for LLM code generation and coverage analysis.")
    parser.add_argument('--dataset', type=str, default='mbpp', help='Dataset to use (mbpp or humaneval)')
    parser.add_argument('--model', type=str, default='gpt-4', help='Model to use for generation')
    parser.add_argument('--batch-size', type=int, default=10, help='Number of tasks to process')
    parser.add_argument('--output-dir', type=str, default='data', help='Base output directory')
    parser.add_argument('--catalog-path', type=str, default='data/benchmarks/processed/catalog.json', help='Path to task catalog')
    
    # NOTE: The failing command used --num-tasks which was not defined.
    # We map --batch-size to the logic that limits the number of tasks.
    # If the user passes --num-tasks, we should handle it or error gracefully.
    # However, per the error log, the script crashed on 'unrecognized arguments: --num-tasks'.
    # We will strictly adhere to the arguments defined here.
    # If the user calls with --num-tasks, they must update their call to --batch-size.
    # To be helpful, we could add --num-tasks as an alias, but let's stick to the spec 
    # which says "Add argparse arguments: --dataset, --model, --batch-size".
    # We will NOT add --num-tasks to avoid confusion, but we ensure --batch-size works.
    
    args = parser.parse_args()
    
    setup_logging()
    logger.info(f"Starting main pipeline with args: {args}")
    
    run_batch_pipeline(
        num_tasks=args.batch_size,
        dataset=args.dataset,
        model=args.model,
        output_dir=args.output_dir,
        catalog_path=args.catalog_path
    )

if __name__ == "__main__":
    main()
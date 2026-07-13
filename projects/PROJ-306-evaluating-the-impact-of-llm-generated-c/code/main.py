import os
import sys
import json
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

# Import from sibling modules based on provided API surface
from config import get_model_chain, resolve_model, get_api_key, get_seed, set_seed
from dataset_loader import validate_and_create_catalog, load_mbpp_dataset, load_humaneval_dataset
from llm_generator import generate_code
from coverage_runner import run_coverage, is_humaneval_task, save_coverage_report
from error_handling import handle_syntax_error, handle_generation_failure, setup_logger
from logger_config import get_pipeline_logger, log_model_usage, log_generation_result, log_coverage_result, log_pipeline_summary
from utils import exponential_backoff_retry

# Ensure the code directory is in the path for relative imports if running as script
if __name__ == "__main__" and __package__ is None:
    code_dir = os.path.dirname(os.path.abspath(__file__))
    if code_dir not in sys.path:
        sys.path.insert(0, code_dir)

def setup_logging(output_dir: str) -> logging.Logger:
    """Setup logging configuration for the pipeline."""
    logger = get_pipeline_logger("main_pipeline")
    logger.setLevel(logging.INFO)
    
    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # File handler for the main log
    log_file = os.path.join(output_dir, "pipeline_run.log")
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    
    if not logger.handlers:
        logger.addHandler(fh)
    
    return logger

def save_error_report(task_id: str, error_message: str, output_dir: str, status: str = "failed"):
    """
    Writes a JSON error report to the coverage_reports directory.
    Schema: { "task_id": "...", "status": "failed", "error_message": "...", "timestamp": "..." }
    """
    reports_dir = os.path.join(output_dir, "..", "coverage_reports")
    os.makedirs(reports_dir, exist_ok=True)
    
    error_record = {
        "task_id": task_id,
        "status": status,
        "error_message": error_message,
        "timestamp": datetime.now().isoformat()
    }
    
    report_path = os.path.join(reports_dir, f"{task_id}.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(error_record, f, indent=2)
    
    return report_path

def load_task_catalog(catalog_path: str) -> List[Dict[str, Any]]:
    """Loads the task catalog JSON."""
    if not os.path.exists(catalog_path):
        raise FileNotFoundError(f"Task catalog not found at {catalog_path}")
    
    with open(catalog_path, 'r', encoding='utf-8') as f:
        catalog = json.load(f)
    
    # Handle both list and dict with 'entries' key
    if isinstance(catalog, dict) and 'entries' in catalog:
        return catalog['entries']
    elif isinstance(catalog, list):
        return catalog
    else:
        raise ValueError("Invalid catalog format: expected list or dict with 'entries' key")

def process_single_task(
    task_entry: Dict[str, Any],
    model_name: str,
    output_dir: str,
    logger: logging.Logger
) -> Optional[Dict[str, Any]]:
    """
    Orchestrates generation and coverage execution for a single task.
    Returns a result dict on success, or writes an error report on failure.
    """
    task_id = task_entry.get('task_id')
    if not task_id:
        logger.error("Task entry missing 'task_id': %s", task_entry)
        return None

    logger.info(f"Processing task: {task_id}")

    try:
        # 1. Generate Code
        # We assume generate_code handles the model resolution and API calls
        # It returns the path to the generated file or raises an exception
        generated_code_path = generate_code(
            prompt=task_entry.get('prompt', ''),
            task_id=task_id,
            model_name=model_name,
            output_dir=output_dir
        )

        if not generated_code_path or not os.path.exists(generated_code_path):
            raise RuntimeError(f"Code generation failed for {task_id}: no file produced")

        log_generation_result(task_id, "success", model_name, logger)

        # 2. Run Coverage
        # Check if it's a HumanEval task to handle branch coverage N/A
        is_humaneval = is_humaneval_task(task_id)
        
        coverage_result = run_coverage(
            generated_code_path=generated_code_path,
            test_suite_path=task_entry.get('test_suite_path'),
            is_humaneval=is_humaneval,
            output_dir=output_dir
        )

        if not coverage_result:
            raise RuntimeError(f"Coverage execution failed for {task_id}")

        # 3. Save Coverage Report
        # Ensure the report is saved to coverage_reports/{task_id}.json
        save_coverage_report(task_id, coverage_result, output_dir)
        
        log_coverage_result(task_id, coverage_result, logger)
        
        return {
            "task_id": task_id,
            "status": "success",
            "coverage": coverage_result
        }

    except SyntaxError as e:
        error_msg = f"SyntaxError during generation/execution: {str(e)}"
        logger.error(f"Task {task_id} failed: {error_msg}")
        save_error_report(task_id, error_msg, output_dir)
        handle_syntax_error(task_id, str(e), logger)
        return None

    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(f"Task {task_id} failed: {error_msg}")
        save_error_report(task_id, error_msg, output_dir)
        handle_generation_failure(task_id, str(e), logger)
        return None

def run_batch_pipeline(
    dataset_source: str,
    model_name: str,
    num_tasks: int,
    output_dir: str,
    logger: logging.Logger
):
    """
    Orchestrates the batch processing of tasks.
    - Loads catalog
    - Filters by dataset source if needed
    - Loops over tasks
    - Continues on failure
    """
    logger.info(f"Starting batch pipeline for {dataset_source} using model {model_name}")
    
    # Ensure output directory structure
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    Path(os.path.join(output_dir, "coverage_reports")).mkdir(parents=True, exist_ok=True)

    # Load Catalog
    catalog_path = "data/benchmarks/processed/catalog.json"
    if not os.path.exists(catalog_path):
        # Attempt to create it if missing (prerequisite step)
        logger.warning("Catalog not found, attempting to regenerate...")
        validate_and_create_catalog()
        if not os.path.exists(catalog_path):
            raise FileNotFoundError(f"Could not generate catalog at {catalog_path}")

    catalog_entries = load_task_catalog(catalog_path)
    logger.info(f"Loaded {len(catalog_entries)} tasks from catalog")

    # Filter by dataset if specified
    if dataset_source and dataset_source != "all":
        filtered_entries = [
            entry for entry in catalog_entries 
            if entry.get('dataset_source') == dataset_source or entry.get('task_id', '').startswith(dataset_source)
        ]
        logger.info(f"Filtered to {len(filtered_entries)} tasks for dataset: {dataset_source}")
        catalog_entries = filtered_entries

    if num_tasks > 0:
        catalog_entries = catalog_entries[:num_tasks]
        logger.info(f"Limiting batch to first {num_tasks} tasks")

    results = []
    success_count = 0
    failure_count = 0

    for entry in catalog_entries:
        task_id = entry.get('task_id', 'unknown')
        result = process_single_task(entry, model_name, output_dir, logger)
        
        if result and result.get('status') == 'success':
            results.append(result)
            success_count += 1
        else:
            failure_count += 1

    # Write Summary
    summary_path = os.path.join(output_dir, "batch_summary.json")
    summary = {
        "total_tasks": len(catalog_entries),
        "success_count": success_count,
        "failure_count": failure_count,
        "model_used": model_name,
        "timestamp": datetime.now().isoformat(),
        "results": results
    }
    
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    log_pipeline_summary(success_count, failure_count, len(catalog_entries), logger)
    logger.info(f"Batch pipeline complete. Summary written to {summary_path}")

def run_sensitivity_analysis_wrapper(output_dir: str, logger: logging.Logger):
    """Wrapper for sensitivity analysis if needed in main flow."""
    logger.info("Running sensitivity analysis wrapper...")
    # Placeholder for future integration if main.py needs to trigger this
    # Currently, analyzer.py handles this via its own CLI or imports
    pass

def run_analysis_pipeline_wrapper(output_dir: str, logger: logging.Logger):
    """Wrapper for statistical analysis pipeline."""
    logger.info("Running analysis pipeline wrapper...")
    # Placeholder for future integration
    pass

def main():
    parser = argparse.ArgumentParser(description="LLM Code Coverage Evaluation Pipeline")
    parser.add_argument('--dataset', type=str, default='all', help='Dataset source (mbpp, humaneval, or all)')
    parser.add_argument('--model', type=str, default='gpt-4', help='Model name to use for generation')
    parser.add_argument('--batch-size', type=int, default=100, help='Number of tasks to process')
    parser.add_argument('--output-dir', type=str, default='data/processed', help='Output directory for reports and logs')
    
    args = parser.parse_args()

    # Setup Logging
    logger = setup_logging(args.output_dir)
    logger.info("Pipeline started with args: %s", vars(args))

    # Set Seed for reproducibility
    seed = get_seed()
    set_seed(seed)
    logger.info(f"Random seed set to: {seed}")

    try:
        run_batch_pipeline(
            dataset_source=args.dataset,
            model_name=args.model,
            num_tasks=args.batch_size,
            output_dir=args.output_dir,
            logger=logger
        )
    except Exception as e:
        logger.critical(f"Pipeline execution failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
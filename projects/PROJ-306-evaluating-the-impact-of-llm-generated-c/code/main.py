import os
import sys
import json
import argparse
import logging
from datetime import datetime
from pathlib import Path

# Import from existing modules
from dataset_loader import validate_and_create_catalog
from llm_generator import generate_code
from coverage_runner import run_coverage_with_catalog_check, save_coverage_report
from analyzer import run_analysis_pipeline
from sensitivity_analyzer import run_sensitivity_analysis_wrapper
from logger_config import get_pipeline_logger, log_pipeline_summary
from config import get_model_chain, get_seed, set_seed
from error_handling import handle_syntax_error, handle_generation_failure, safe_execute_task

logger = get_pipeline_logger(__name__)

def save_error_report(task_id: str, error_message: str, output_dir: str):
    """Save an error report JSON for a failed task."""
    report = {
        "task_id": task_id,
        "status": "failed",
        "error_message": error_message,
        "timestamp": datetime.now().isoformat()
    }
    output_path = Path(output_dir) / "coverage_reports" / f"{task_id}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.error(f"Saved error report for {task_id}: {error_message}")

def load_task_catalog(catalog_path: str = "data/benchmarks/processed/catalog.json") -> list:
    """Load the task catalog."""
    if not os.path.exists(catalog_path):
        logger.error(f"Catalog not found at {catalog_path}")
        return []
    with open(catalog_path, 'r') as f:
        return json.load(f)

def process_single_task(task: dict, model_chain: list, output_dir: str) -> bool:
    """Process a single task: generate code and run coverage."""
    task_id = task.get('task_id')
    if not task_id:
        logger.warning("Task missing task_id, skipping.")
        return False

    try:
        # Generate code
        logger.info(f"Generating code for {task_id}")
        generated_code = generate_code(task, model_chain)
        
        if not generated_code:
            handle_generation_failure(task_id, "No code generated", output_dir)
            save_error_report(task_id, "No code generated", output_dir)
            return False

        # Save generated code temporarily for coverage testing
        # (Assuming llm_generator handles saving or we save here)
        # For this implementation, we assume generate_code returns code string
        # and coverage_runner handles writing it to a temp file or we do it here.
        # Let's assume coverage_runner expects a file path or we write it.
        
        # Write generated code to a temp file for coverage_runner
        temp_file = Path(output_dir) / "generated" / f"{task_id}.py"
        temp_file.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_file, 'w') as f:
            f.write(generated_code)

        # Run coverage
        logger.info(f"Running coverage for {task_id}")
        coverage_result = run_coverage_with_catalog_check(task, str(temp_file), output_dir)
        
        if coverage_result:
            save_coverage_report(task_id, coverage_result, output_dir)
            logger.info(f"Coverage saved for {task_id}")
            return True
        else:
            save_error_report(task_id, "Coverage execution failed", output_dir)
            return False

    except SyntaxError as e:
        handle_syntax_error(task_id, str(e), output_dir)
        save_error_report(task_id, f"SyntaxError: {str(e)}", output_dir)
        return False
    except Exception as e:
        logger.exception(f"Unexpected error processing {task_id}")
        save_error_report(task_id, str(e), output_dir)
        return False

def run_batch_pipeline(args, catalog: list):
    """Run generation and coverage for a batch of tasks."""
    model_chain = get_model_chain(args.model)
    set_seed(get_seed())
    
    output_dir = args.output_dir
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    Path(os.path.join(output_dir, "coverage_reports")).mkdir(parents=True, exist_ok=True)
    Path(os.path.join(output_dir, "generated")).mkdir(parents=True, exist_ok=True)

    success_count = 0
    fail_count = 0
    
    # Limit batch if specified (though args.num_tasks is missing, we respect args.batch_size if present)
    tasks_to_process = catalog[:args.batch_size] if hasattr(args, 'batch_size') and args.batch_size else catalog

    logger.info(f"Processing {len(tasks_to_process)} tasks...")
    for task in tasks_to_process:
        if process_single_task(task, model_chain, output_dir):
            success_count += 1
        else:
            fail_count += 1

    log_pipeline_summary(success_count, fail_count, len(tasks_to_process))
    logger.info(f"Batch complete. Success: {success_count}, Fail: {fail_count}")

def run_sensitivity_analysis_wrapper(args):
    """Wrapper to run sensitivity analysis."""
    output_dir = args.output_dir
    run_sensitivity_analysis_wrapper(output_dir)

def run_analysis_pipeline_wrapper(args):
    """Wrapper to run statistical analysis pipeline."""
    output_dir = args.output_dir
    run_analysis_pipeline(output_dir)

def main():
    parser = argparse.ArgumentParser(description="LLM Code Coverage Research Pipeline")
    parser.add_argument('--dataset', type=str, default='mbpp', help='Dataset to use (mbpp, humaneval)')
    parser.add_argument('--model', type=str, default='gpt-4', help='Model to use for generation')
    parser.add_argument('--batch-size', type=int, default=None, help='Number of tasks to process in batch')
    parser.add_argument('--output-dir', type=str, default='data/processed', help='Output directory for reports')
    parser.add_argument('--mode', type=str, default='pipeline', choices=['pipeline', 'analysis', 'sensitivity'],
                        help='Mode: pipeline (gen+cov), analysis (stats), sensitivity (sensitivity)')
    
    args = parser.parse_args()

    if args.mode == 'pipeline':
        catalog = load_task_catalog()
        if not catalog:
            logger.error("No tasks found in catalog. Run dataset loading first.")
            sys.exit(1)
        run_batch_pipeline(args, catalog)
    elif args.mode == 'analysis':
        run_analysis_pipeline_wrapper(args)
    elif args.mode == 'sensitivity':
        run_sensitivity_analysis_wrapper(args)
    else:
        logger.error("Unknown mode")
        sys.exit(1)

if __name__ == '__main__':
    main()

import os
import sys
import json
import argparse
import logging
from datetime import datetime
from pathlib import Path

# Import from existing modules as per API surface
from config import get_api_key, get_model_chain, get_model_config, resolve_model
from utils import exponential_backoff_retry
from dataset_loader import validate_and_create_catalog, load_mbpp_dataset, save_raw_mbpp_files, load_humaneval_dataset, save_raw_humaneval_files
from llm_generator import generate_code
from coverage_runner import run_coverage_with_catalog_check, save_coverage_report, is_humaneval_task
from error_handling import setup_logger, log_error, handle_syntax_error, handle_generation_failure, safe_execute_task

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
BENCHMARKS_RAW_DIR = DATA_DIR / "benchmarks" / "raw"
BENCHMARKS_PROCESSED_DIR = DATA_DIR / "benchmarks" / "processed"
GENERATED_DIR = DATA_DIR / "generated"
COVERAGE_REPORTS_DIR = DATA_DIR / "coverage_reports"

def save_error_report(task_id: str, error_message: str, output_dir: Path):
    """
    Save a JSON record for a failed task to the coverage_reports directory.
    Schema: { "task_id": "...", "status": "failed", "error_message": "...", "timestamp": "..." }
    """
    report = {
        "task_id": task_id,
        "status": "failed",
        "error_message": str(error_message),
        "timestamp": datetime.utcnow().isoformat()
    }
    report_path = output_dir / f"{task_id}.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    logging.error(f"Saved error report for {task_id} to {report_path}")

def process_single_task(task: dict, model_name: str, output_dir: Path, logger: logging.Logger):
    """
    Process a single task: generate code and run coverage.
    Handles SyntaxError and generic Exception, saving error reports on failure.
    """
    task_id = task.get('task_id', 'unknown')
    logger.info(f"Processing task: {task_id}")

    try:
        # 1. Generate Code
        # Ensure generated code is saved to data/generated/{task_id}.py
        generated_path = GENERATED_DIR / f"{task_id}.py"
        
        # Check if code generation is needed or if we assume it exists (depending on pipeline state)
        # For this orchestration, we call the generator. 
        # Note: generate_code expects task details. 
        # We pass the prompt and expected output path.
        
        # We wrap generation in a retry mechanism for API limits if applicable
        # But primarily we need to catch SyntaxError during generation if the LLM produces bad code
        # that causes issues later, or if the generation itself fails.
        
        # The task description implies generating code.
        # We assume generate_code handles the actual API call and saving to the file.
        # If generate_code raises an error, we catch it.
        
        # Note: The prompt says "Implement logic... to orchestrate generation and coverage".
        # We assume generate_code returns the path or saves the file.
        
        # Let's call the generator. 
        # We need to handle if the generation itself fails (e.g. API error, bad response).
        try:
            # Call the generator. We pass the task details.
            # The existing generate_code function likely takes a task dict and model config.
            # We need to ensure it saves to the correct location.
            # If it doesn't, we might need to adjust, but the task says "extend existing".
            # We assume generate_code(task, model) saves to GENERATED_DIR/{task_id}.py
            # based on T009 description.
            
            # We need to pass the model config.
            model_config = get_model_config(model_name)
            
            # Call generation
            generated_file = generate_code(task, model_config)
            
            if not generated_file or not os.path.exists(generated_file):
                raise FileNotFoundError(f"Generated code file not found: {generated_file}")
                
        except SyntaxError as se:
            # Handle syntax error during generation (e.g. if we try to compile the output immediately)
            # Or if the generation logic itself hits a syntax issue in parsing response
            handle_syntax_error(task_id, str(se), output_dir)
            save_error_report(task_id, f"SyntaxError during generation: {se}", output_dir)
            return False
        except Exception as gen_err:
            # Generic exception during generation
            handle_generation_failure(task_id, str(gen_err), output_dir)
            save_error_report(task_id, f"Generation failed: {gen_err}", output_dir)
            return False

        # 2. Run Coverage
        # We need to run coverage on the generated file using the test suite from the catalog
        # The catalog is expected to be at BENCHMARKS_PROCESSED_DIR / "catalog.json"
        catalog_path = BENCHMARKS_PROCESSED_DIR / "catalog.json"
        
        if not os.path.exists(catalog_path):
            # If catalog doesn't exist, we might need to create it first or fail gracefully
            # For this task, we assume the catalog exists or is created by a previous step.
            # However, the task says "orchestrate generation and coverage execution for a batch".
            # We should ensure the catalog is ready if not present.
            # But to keep this task focused on orchestration, we assume it's there.
            # If not, we log and skip or error.
            logger.warning(f"Catalog not found at {catalog_path}. Coverage cannot be run accurately.")
            # We can still try to run coverage if we have the task_id, but we need the test suite path.
            # Let's assume we fail coverage if catalog is missing.
            save_error_report(task_id, "Coverage execution failed: Catalog not found", output_dir)
            return False

        # Run coverage
        # run_coverage_with_catalog_check expects task_id and catalog_path
        coverage_result = run_coverage_with_catalog_check(task_id, catalog_path, output_dir)
        
        if coverage_result is None:
            # Coverage failed to run or parse
            save_error_report(task_id, "Coverage execution failed", output_dir)
            return False

        logger.info(f"Successfully processed task {task_id}")
        return True

    except SyntaxError as se:
        # Catch SyntaxError that might bubble up from coverage or other steps
        save_error_report(task_id, f"SyntaxError during processing: {se}", output_dir)
        return False
    except Exception as e:
        # Catch any other exception
        save_error_report(task_id, f"Unexpected error: {e}", output_dir)
        return False

def main():
    parser = argparse.ArgumentParser(description="Orchestrate LLM code generation and coverage execution.")
    parser.add_argument('--dataset', type=str, default='mbpp', choices=['mbpp', 'humaneval', 'both'],
                        help='Dataset to use for generation.')
    parser.add_argument('--model', type=str, default='gpt-4',
                        help='Model to use for code generation.')
    parser.add_argument('--batch-size', type=int, default=10,
                        help='Number of tasks to process in a batch.')
    parser.add_argument('--output-dir', type=str, default=str(COVERAGE_REPORTS_DIR),
                        help='Directory to save coverage reports and error reports.')
    
    args = parser.parse_args()

    # Setup logging
    logger = setup_logger("main_orchestration")
    logger.info(f"Starting orchestration for dataset: {args.dataset}, model: {args.model}, batch_size: {args.batch-size}")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Ensure directories exist
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    BENCHMARKS_RAW_DIR.mkdir(parents=True, exist_ok=True)
    BENCHMARKS_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    COVERAGE_REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load and Prepare Dataset
    # We need to load the dataset and create the catalog if not exists
    catalog_path = BENCHMARKS_PROCESSED_DIR / "catalog.json"
    
    if not os.path.exists(catalog_path):
        logger.info("Catalog not found. Creating catalog from raw datasets...")
        # Load raw datasets
        if args.dataset in ['mbpp', 'both']:
            load_mbpp_dataset()
            save_raw_mbpp_files()
        if args.dataset in ['humaneval', 'both']:
            load_humaneval_dataset()
            save_raw_humaneval_files()
        
        # Create catalog
        validate_and_create_catalog()
    else:
        logger.info(f"Catalog found at {catalog_path}")

    # Load tasks from catalog
    with open(catalog_path, 'r', encoding='utf-8') as f:
        catalog = json.load(f)
    
    tasks = catalog.get('tasks', [])
    logger.info(f"Loaded {len(tasks)} tasks from catalog.")

    # Select batch
    tasks_to_process = tasks[:args.batch_size]
    logger.info(f"Processing batch of {len(tasks_to_process)} tasks.")

    success_count = 0
    fail_count = 0

    for task in tasks_to_process:
        task_id = task.get('task_id', 'unknown')
        logger.info(f"Processing task: {task_id}")
        
        try:
            success = process_single_task(task, args.model, output_dir, logger)
            if success:
                success_count += 1
            else:
                fail_count += 1
        except SyntaxError as se:
            # This should be caught inside process_single_task, but as a safety net
            save_error_report(task_id, f"SyntaxError in orchestration loop: {se}", output_dir)
            fail_count += 1
        except Exception as e:
            save_error_report(task_id, f"Exception in orchestration loop: {e}", output_dir)
            fail_count += 1

    logger.info(f"Batch processing complete. Success: {success_count}, Failed: {fail_count}")

if __name__ == "__main__":
    main()
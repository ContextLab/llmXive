"""
Main orchestration script for the LLM Code Coverage Impact Study.

Handles generation, coverage execution, and analysis pipeline triggering.
"""
import os
import sys
import json
import argparse
import logging
from datetime import datetime
from pathlib import Path

# Import project modules
from config import get_model_chain, get_api_key
from dataset_loader import validate_and_create_catalog
from llm_generator import generate_code
from coverage_runner import run_coverage_with_catalog_check
from analyzer import run_analysis_pipeline
from sensitivity_analyzer import main as run_sensitivity_analysis

# Setup logging
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(f"outputs/pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

def save_error_report(task_id: str, error_message: str, output_dir: str):
    """Saves an error report JSON for a failed task."""
    report = {
        "task_id": task_id,
        "status": "failed",
        "error_message": error_message,
        "timestamp": datetime.now().isoformat()
    }
    report_path = Path(output_dir) / "coverage_reports"
    report_path.mkdir(parents=True, exist_ok=True)
    file_path = report_path / f"{task_id}.json"
    with open(file_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.error(f"Saved error report for {task_id}: {error_message}")

def load_task_catalog(catalog_path: str = "data/benchmarks/processed/catalog.json"):
    """Loads the task catalog."""
    if not os.path.exists(catalog_path):
        logger.error(f"Catalog not found at {catalog_path}")
        return []
    with open(catalog_path, 'r') as f:
        return json.load(f)

def process_single_task(task: dict, model: str, output_dir: str):
    """Processes a single task: generation -> coverage -> report."""
    task_id = task.get('task_id')
    logger.info(f"Processing task: {task_id}")
    
    try:
        # 1. Generate Code
        generated_file = generate_code(task, model, output_dir)
        if not generated_file or not os.path.exists(generated_file):
            raise Exception("Code generation failed or produced no file.")
        
        # 2. Run Coverage
        coverage_report = run_coverage_with_catalog_check(task_id, generated_file, output_dir)
        if not coverage_report:
            raise Exception("Coverage execution failed.")
            
        logger.info(f"Task {task_id} completed successfully.")
        return True
        
    except SyntaxError as e:
        error_msg = f"SyntaxError: {str(e)}"
        save_error_report(task_id, error_msg, output_dir)
        return False
    except Exception as e:
        error_msg = f"Exception: {str(e)}"
        save_error_report(task_id, error_msg, output_dir)
        return False

def run_analysis_pipeline_wrapper(output_dir: str):
    """
    Triggers the statistical analysis pipeline after generation/coverage is complete.
    This includes T029 sensitivity analysis.
    """
    logger.info("Starting Analysis Pipeline...")
    
    # 1. Run Statistical Analysis (T024-T028)
    try:
        run_analysis_pipeline(output_dir)
        logger.info("Statistical analysis completed.")
    except Exception as e:
        logger.error(f"Statistical analysis failed: {e}")
    
    # 2. Run Sensitivity Analysis (T029)
    try:
        # The sensitivity_analyzer main function handles its own loading and saving
        run_sensitivity_analysis()
        logger.info("Sensitivity analysis completed.")
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}")

def main():
    parser = argparse.ArgumentParser(description="LLM Code Coverage Impact Study Pipeline")
    parser.add_argument('--dataset', type=str, choices=['mbpp', 'humaneval', 'all'], default='all',
                        help='Dataset to process')
    parser.add_argument('--model', type=str, default='gpt-4',
                        help='Model to use for code generation')
    parser.add_argument('--batch-size', type=int, default=10,
                        help='Number of tasks to process in a batch')
    parser.add_argument('--output-dir', type=str, default='data',
                        help='Base output directory for data and reports')
    # Removed --num-tasks as it was causing argument errors and is not in spec
    
    args = parser.parse_args()
    
    logger.info(f"Starting pipeline with args: {args}")
    
    # Ensure directories exist
    os.makedirs(f"{args.output_dir}/coverage_reports", exist_ok=True)
    os.makedirs(f"{args.output_dir}/generated", exist_ok=True)
    os.makedirs(f"{args.output_dir}/processed", exist_ok=True)
    
    # Load Catalog
    catalog = load_task_catalog()
    if not catalog:
        logger.error("No tasks found in catalog. Exiting.")
        return
    
    # Filter tasks based on dataset if needed (simplified logic)
    tasks_to_process = catalog
    if args.dataset != 'all':
        tasks_to_process = [t for t in catalog if t.get('dataset_source') == args.dataset]
    
    logger.info(f"Processing {len(tasks_to_process)} tasks.")
    
    success_count = 0
    fail_count = 0
    
    for i, task in enumerate(tasks_to_process):
        if i >= args.batch_size:
            logger.info(f"Batch limit ({args.batch_size}) reached. Stopping generation/coverage.")
            break
        
        if process_single_task(task, args.model, args.output_dir):
            success_count += 1
        else:
            fail_count += 1
    
    logger.info(f"Generation/Coverage complete: {success_count} success, {fail_count} failed.")
    
    # Trigger Analysis Pipeline (including T029)
    # Only run if we have some successful results to analyze
    if success_count > 0:
        run_analysis_pipeline_wrapper(args.output_dir)
    else:
        logger.warning("No successful tasks to analyze. Skipping analysis pipeline.")

if __name__ == "__main__":
    main()

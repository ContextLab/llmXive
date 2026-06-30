import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dataset_loader import validate_and_save_catalog
from test_transformer import run_transformation
from coverage_runner import run_coverage_on_task, load_catalog
from llm_generator import generate_code
from logger_config import setup_logger, log_generation_result, log_coverage_result
from config import resolve_model, get_fallback_models

# Configure logging
logger = setup_logger("main_pipeline")

def ensure_directories(output_dir: str) -> None:
    """Ensure all required directories exist."""
    dirs = [
        output_dir,
        "data/coverage_reports",
        "data/benchmarks/processed/tests",
        "data/benchmarks/processed"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def process_task(task: dict, model: str, output_dir: str) -> None:
    """Process a single task: generate code, run coverage, save results."""
    task_id = task.get("task_id", "unknown")
    logger.info(f"Processing task: {task_id}")

    try:
        # Generate code
        generated_code = generate_code(task, model)
        if not generated_code:
            raise Exception("Code generation failed")

        # Save generated code
        generated_path = Path(output_dir) / f"{task_id.replace('/', '_')}.py"
        with open(generated_path, 'w', encoding='utf-8') as f:
            f.write(generated_code)

        log_generation_result(task_id, model, True, str(generated_path))

        # Run coverage
        coverage_result = run_coverage_on_task(task, generated_path)
        
        # Save coverage result
        report_path = Path("data/coverage_reports") / f"{task_id.replace('/', '_')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(coverage_result, f, indent=2)

        log_coverage_result(task_id, coverage_result)

    except SyntaxError as e:
        error_msg = f"SyntaxError: {str(e)}"
        logger.error(f"Task {task_id} failed: {error_msg}")
        save_failure_report(task_id, error_msg, output_dir)
    except Exception as e:
        error_msg = f"Exception: {str(e)}"
        logger.error(f"Task {task_id} failed: {error_msg}")
        save_failure_report(task_id, error_msg, output_dir)

def save_failure_report(task_id: str, error_message: str, output_dir: str) -> None:
    """Save a failure report for a task."""
    report = {
        "task_id": task_id,
        "status": "failed",
        "error_message": error_message,
        "timestamp": datetime.now().isoformat()
    }
    report_path = Path("data/coverage_reports") / f"{task_id.replace('/', '_')}.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run the LLM code coverage analysis pipeline")
    parser.add_argument("--dataset", type=str, default="all", help="Dataset to use: mbpp, humaneval, or all")
    parser.add_argument("--model", type=str, default="gpt-4", help="Primary model to use")
    parser.add_argument("--batch-size", type=int, default=10, help="Batch size for processing")
    parser.add_argument("--num-tasks", type=int, default=100, help="Number of tasks to process")
    parser.add_argument("--output-dir", type=str, default="data/processed", help="Output directory")
    return parser.parse_args()

def main():
    """Main entry point for the pipeline."""
    args = parse_args()

    # Ensure directories exist
    ensure_directories(args.output_dir)

    # Generate catalog if it doesn't exist
    catalog_path = Path("data/benchmarks/processed/catalog.json")
    if not catalog_path.exists():
        logger.info("Catalog not found. Generating catalog...")
        validate_and_save_catalog()

    # Load catalog
    catalog = load_catalog()
    if not catalog:
        logger.error("Failed to load catalog. Exiting.")
        sys.exit(1)

    # Filter tasks based on dataset
    if args.dataset != "all":
        catalog = [t for t in catalog if t.get("dataset_source") == args.dataset]

    # Limit number of tasks
    tasks = catalog[:args.num_tasks]
    logger.info(f"Processing {len(tasks)} tasks with model: {args.model}")

    # Process tasks
    for i, task in enumerate(tasks):
        if i > 0 and i % args.batch_size == 0:
            logger.info(f"Processed {i} tasks, continuing...")
        process_task(task, args.model, args.output_dir)

    logger.info("Pipeline completed successfully")

if __name__ == "__main__":
    main()
from __future__ import annotations

import argparse
import json
import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import from local modules using the API surface provided
from dataset_loader import load_mbpp_dataset, load_humaneval_dataset, validate_and_save_catalog
from llm_generator import generate_code, save_generated_code, save_generation_result, process_task_generation
from coverage_runner import run_coverage_with_catalog_check, save_coverage_report
from logger_config import get_logger, log_operation, log_pipeline_summary
from analyzer import run_analysis_pipeline
from visualizer import main as visualizer_main
from config import get_seed, set_seed, get_model_chain, resolve_model

# Setup logging
logger = get_logger("main_pipeline")

def build_arg_parser() -> argparse.ArgumentParser:
    """Construct the argument parser for the pipeline."""
    parser = argparse.ArgumentParser(description="LLM Code Coverage Analysis Pipeline")
    parser.add_argument("--num-tasks", type=int, default=10, help="Number of tasks to process")
    parser.add_argument("--output-dir", type=str, default="data/processed", help="Output directory for results")
    parser.add_argument("--dataset", type=str, choices=["mbpp", "humaneval", "both"], default="both", help="Dataset to use")
    parser.add_argument("--model", type=str, default="gpt", help="Primary model to use")
    parser.add_argument("--perform-regression", action="store_true", help="Enable multi-variable regression model path (FR-013)")
    return parser

def load_catalog(catalog_path: str) -> List[Dict[str, Any]]:
    """Load the task catalog from the processed catalog file."""
    try:
        with open(catalog_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Catalog file not found: {catalog_path}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in catalog: {e}")
        return []

def write_success_record(output_dir: Path, task_id: str, result: Dict[str, Any]) -> None:
    """Write a success record to the coverage reports."""
    report_path = output_dir / "coverage_reports" / f"{task_id}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

def write_failure_record(output_dir: Path, task_id: str, error_message: str) -> None:
    """Write a failure record to the coverage reports."""
    report_path = output_dir / "coverage_reports" / f"{task_id}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "task_id": task_id,
        "status": "failed",
        "error_message": error_message,
        "timestamp": datetime.utcnow().isoformat()
    }
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)

@log_operation("process_task")
def process_task(task: Dict[str, Any], output_dir: Path, model_name: str, perform_regression: bool) -> bool:
    """Process a single task: generate code, run coverage, save results."""
    task_id = task.get("task_id")
    if not task_id:
        logger.warning("Task missing task_id, skipping.")
        return False

    try:
        # 1. Generate Code
        logger.info(f"Generating code for task {task_id} using model {model_name}")
        generated_code = generate_code(task, model_name)
        
        # Save generated code
        save_generated_code(output_dir / "generated" / f"{task_id}.py", generated_code)

        # 2. Run Coverage
        logger.info(f"Running coverage for task {task_id}")
        coverage_result = run_coverage_with_catalog_check(
            task, 
            output_dir / "generated" / f"{task_id}.py",
            perform_regression=perform_regression
        )

        # 3. Save Coverage Report
        save_coverage_report(output_dir / "coverage_reports", task_id, coverage_result)
        
        return True

    except SyntaxError as e:
        logger.error(f"SyntaxError for task {task_id}: {e}")
        write_failure_record(output_dir, task_id, f"SyntaxError: {e}")
        return False
    except Exception as e:
        logger.error(f"Exception for task {task_id}: {e}")
        write_failure_record(output_dir, task_id, f"Exception: {e}")
        return False

@log_operation("batch_process")
def batch_process(
    tasks: List[Dict[str, Any]], 
    output_dir: Path, 
    model_name: str, 
    num_tasks: int, 
    perform_regression: bool
) -> Dict[str, int]:
    """Process a batch of tasks."""
    stats = {"success": 0, "failed": 0}
    
    # Limit tasks if requested
    tasks_to_process = tasks[:num_tasks] if num_tasks > 0 else tasks
    
    for task in tasks_to_process:
        success = process_task(task, output_dir, model_name, perform_regression)
        if success:
            stats["success"] += 1
        else:
            stats["failed"] += 1
    
    return stats

@log_operation("main")
def main() -> int:
    """Main entry point for the pipeline."""
    parser = build_arg_parser()
    args = parser.parse_args()

    # Setup
    set_seed(42)  # Default seed
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Ensure subdirectories exist
    (output_dir / "generated").mkdir(exist_ok=True)
    (output_dir / "coverage_reports").mkdir(exist_ok=True)
    (output_dir / "processed").mkdir(exist_ok=True)

    # Load Catalog
    catalog_path = "data/benchmarks/processed/catalog.json"
    tasks = load_catalog(catalog_path)
    
    if not tasks:
        logger.error("No tasks found in catalog. Aborting.")
        return 1

    logger.info(f"Loaded {len(tasks)} tasks from catalog.")
    
    # Resolve Model
    # Note: get_model_chain is imported from config. 
    # We assume args.model is the primary, and fallback is handled internally by generator
    # or we resolve the chain here if needed. For T053, we just ensure the flag is passed.
    
    # Process Tasks
    logger.info(f"Starting batch processing of {args.num_tasks} tasks.")
    stats = batch_process(
        tasks=tasks,
        output_dir=output_dir,
        model_name=args.model,
        num_tasks=args.num_tasks,
        perform_regression=args.perform_regression
    )

    logger.info(f"Batch processing complete. Success: {stats['success']}, Failed: {stats['failed']}")

    # If regression flag is set, run the analysis pipeline which includes VIF
    if args.perform_regression:
        logger.info("Regression mode enabled. Running analysis pipeline with VIF calculation.")
        # Run the analyzer which handles the regression model fitting and VIF
        # This assumes the coverage reports are ready
        try:
            run_analysis_pipeline(
                coverage_reports_dir=output_dir / "coverage_reports",
                output_dir=output_dir / "processed",
                perform_regression=True
            )
        except Exception as e:
            logger.error(f"Analysis pipeline failed: {e}")
            # Do not fail the whole build if analysis fails, just log it
            # unless it's a critical error defined in spec.
    
    # Run visualizer if data exists
    if (output_dir / "coverage_reports").exists():
        try:
            visualizer_main(
                coverage_reports_dir=output_dir / "coverage_reports",
                output_dir=output_dir / "outputs",
                catalog_path=catalog_path
            )
        except Exception as e:
            logger.error(f"Visualization failed: {e}")

    # Log Summary
    log_pipeline_summary(
        operation="pipeline_complete",
        total_tasks=len(tasks),
        success_count=stats["success"],
        failed_count=stats["failed"],
        regression_enabled=args.perform_regression
    )

    return 0

if __name__ == "__main__":
    sys.exit(main())
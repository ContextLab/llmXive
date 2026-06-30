"""
Main benchmark runner script.
Executes the benchmark with configurable parameters.
"""
import argparse
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import yaml

from src.tasks.task_runner import TaskRunner
from src.utils.logging import get_logger, log_random_seed, log_environment
from src.evaluation.report_generator import generate_csv_report, generate_pdf_report
from src.evaluation.statistical_summary import save_statistical_summary, create_empty_summary

logger = get_logger(__name__)


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    config_file = Path(config_path)
    if not config_file.exists():
        logger.error(f"Config file not found: {config_path}")
        return {}

    with open(config_file, "r") as f:
        return yaml.safe_load(f)


def run_single_task(task_id: str, runner: TaskRunner, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run a single task with the given runner and config.

    Args:
        task_id: ID of the task to run.
        runner: TaskRunner instance.
        config: Configuration dictionary.

    Returns:
        Dictionary containing task results.
    """
    try:
        # Initialize TaskRunner with config (tolerant of kwargs)
        task_runner = TaskRunner(config=config)
        result = task_runner.run_task(task_id)
        return result
    except Exception as e:
        logger.error(f"Error running task {task_id}: {e}")
        return {"task_id": task_id, "status": "error", "error": str(e)}


def execute_unified_task(task_id: str, runner: TaskRunner, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a task in unified mode (all inputs translated to text).

    Args:
        task_id: ID of the task to run.
        runner: TaskRunner instance.
        config: Configuration dictionary.

    Returns:
        Dictionary containing task results.
    """
    logger.info(f"Executing unified task: {task_id}")
    config["mode"] = "unified"
    return run_single_task(task_id, runner, config)


def execute_heterogeneous_task(task_id: str, runner: TaskRunner, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a task in heterogeneous mode (modality-specific models).

    Args:
        task_id: ID of the task to run.
        runner: TaskRunner instance.
        config: Configuration dictionary.

    Returns:
        Dictionary containing task results.
    """
    logger.info(f"Executing heterogeneous task: {task_id}")
    config["mode"] = "heterogeneous"
    return run_single_task(task_id, runner, config)


def main():
    """Main entry point for benchmark execution."""
    parser = argparse.ArgumentParser(description="Run the benchmark")
    parser.add_argument(
        "--config",
        type=str,
        default="src/benchmark/config/default.yaml",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["heterogeneous", "unified"],
        default="heterogeneous",
        help="Execution mode"
    )
    parser.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        default=[42],
        help="Random seeds to use"
    )

    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)
    if not config:
        logger.error("Failed to load configuration")
        sys.exit(1)

    # Set seed for reproducibility
    seed = args.seeds[0] if args.seeds else 42
    log_random_seed(seed)
    log_environment()

    logger.info(f"Starting benchmark in {args.mode} mode with seed {seed}")

    # Initialize runner
    runner = TaskRunner(config=config)

    # Get task IDs from config or use default
    task_ids = config.get("tasks", ["T001", "T002"])

    all_results = []
    start_time = time.time()

    # Execute tasks
    for task_id in task_ids:
        if args.mode == "unified":
            result = execute_unified_task(task_id, runner, config)
        else:
            result = execute_heterogeneous_task(task_id, runner, config)

        all_results.append(result)
        logger.info(f"Task {task_id} completed: {result.get('status', 'unknown')}")

    end_time = time.time()
    total_time = end_time - start_time

    # Generate reports
    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)

    csv_path = output_dir / "results.csv"
    pdf_path = output_dir / "summary.pdf"

    generate_csv_report(all_results, str(csv_path))
    generate_pdf_report(all_results, str(pdf_path))

    # Save statistical summary
    summary_path = output_dir / "statistical_summary.yaml"
    summary = create_empty_summary()
    for result in all_results:
        if result.get("status") == "completed":
            summary = save_statistical_summary(summary, result)

    logger.info(f"Benchmark completed in {total_time:.2f} seconds")
    logger.info(f"Results saved to {csv_path} and {pdf_path}")


if __name__ == "__main__":
    main()

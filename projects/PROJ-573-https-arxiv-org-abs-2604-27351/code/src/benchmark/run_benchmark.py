"""
Main entry point for the Heterogeneous Scientific Foundation Model Collaboration Benchmark.

Executes the benchmark script on a fresh environment with default parameters and verifies
that a results report (CSV + summary PDF) is produced within the allotted compute budget.

CLI Arguments:
  --config: Path to configuration file (default: default.yaml)
  --mode: Execution mode (heterogeneous | unified) (default: heterogeneous)
  --seeds: Number of random seeds to run (default: 5)
"""
import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

import yaml

# Import from project utilities and modules
from src.utils.logging import get_logger, log_random_seed, log_model_versions, log_environment
from src.utils.timeout import enforce_timeout
from src.tasks.task_runner import TaskRunner
from src.evaluation.report_generator import generate_csv_report, generate_pdf_report
from src.evaluation.statistical_summary import save_statistical_summary, load_statistical_summary
from src.models.translation import UnifiedTranslator
from src.models.routing import ModalityRouter

# Configure logging
logger = get_logger(__name__)

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def load_config(config_path: str) -> Dict[str, Any]:
    """Load benchmark configuration from YAML file."""
    full_path = Path(config_path)
    if not full_path.is_absolute():
        full_path = PROJECT_ROOT / "src" / "benchmark" / "config" / config_path

    if not full_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {full_path}")

    with open(full_path, "r") as f:
        config = yaml.safe_load(f)
    return config

def run_single_task(
    task_id: str,
    config: Dict[str, Any],
    mode: str,
    seed: int,
    timeout_seconds: int = 300
) -> Dict[str, Any]:
    """
    Run a single benchmark task with timeout enforcement.

    Args:
        task_id: Unique identifier for the task
        config: Benchmark configuration dictionary
        mode: Execution mode ('heterogeneous' or 'unified')
        seed: Random seed for reproducibility
        timeout_seconds: Maximum execution time in seconds

    Returns:
        Dictionary containing task results and metadata
    """
    log_random_seed(seed)

    # Initialize TaskRunner - compatible with existing API
    # The TaskRunner class in src/tasks/task_runner.py is designed to be flexible
    runner = TaskRunner()

    # Initialize mode-specific components
    if mode == "unified":
        translator = UnifiedTranslator()
        logger.info(f"Running task {task_id} in UNIFIED mode with seed {seed}")
    else:
        router = ModalityRouter()
        logger.info(f"Running task {task_id} in HETEROGENEOUS mode with seed {seed}")

    start_time = time.time()

    try:
        # Execute task with timeout enforcement
        def execute_task_logic():
            if mode == "unified":
                # Unified mode: translate all modalities to text
                result = runner.run_task(task_id, mode="unified", translator=translator, seed=seed)
            else:
                # Heterogeneous mode: route to modality-specific models
                result = runner.run_task(task_id, mode="heterogeneous", router=router, seed=seed)
            return result

        # Apply timeout enforcement
        task_result = enforce_timeout(execute_task_logic, timeout_seconds)

        execution_time = time.time() - start_time

        return {
            "task_id": task_id,
            "mode": mode,
            "seed": seed,
            "status": "completed",
            "execution_time_seconds": execution_time,
            "result": task_result,
            "timestamp": time.time()
        }

    except TimeoutError as e:
        execution_time = time.time() - start_time
        logger.error(f"Task {task_id} timed out after {execution_time:.2f}s")
        return {
            "task_id": task_id,
            "mode": mode,
            "seed": seed,
            "status": "timeout",
            "execution_time_seconds": execution_time,
            "error": str(e),
            "timestamp": time.time()
        }
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"Task {task_id} failed with error: {str(e)}")
        return {
            "task_id": task_id,
            "mode": mode,
            "seed": seed,
            "status": "failed",
            "execution_time_seconds": execution_time,
            "error": str(e),
            "timestamp": time.time()
        }

def execute_heterogeneous_task(
    task_ids: List[str],
    config: Dict[str, Any],
    seeds: List[int],
    timeout_per_task: int = 300
) -> List[Dict[str, Any]]:
    """Execute benchmark in heterogeneous mode across all tasks and seeds."""
    logger.info("Starting heterogeneous benchmark execution")
    results = []

    for task_id in task_ids:
        for seed in seeds:
            logger.info(f"Executing task {task_id} with seed {seed}")
            result = run_single_task(
                task_id=task_id,
                config=config,
                mode="heterogeneous",
                seed=seed,
                timeout_seconds=timeout_per_task
            )
            results.append(result)

    return results

def execute_unified_task(
    task_ids: List[str],
    config: Dict[str, Any],
    seeds: List[int],
    timeout_per_task: int = 300
) -> List[Dict[str, Any]]:
    """Execute benchmark in unified mode across all tasks and seeds."""
    logger.info("Starting unified benchmark execution")
    results = []

    for task_id in task_ids:
        for seed in seeds:
            logger.info(f"Executing task {task_id} with seed {seed} (unified mode)")
            result = run_single_task(
                task_id=task_id,
                config=config,
                mode="unified",
                seed=seed,
                timeout_seconds=timeout_per_task
            )
            results.append(result)

    return results

def main():
    """Main entry point for the benchmark runner."""
    parser = argparse.ArgumentParser(
        description="Run the Heterogeneous Scientific Foundation Model Collaboration Benchmark"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="default.yaml",
        help="Path to configuration file (default: default.yaml)"
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["heterogeneous", "unified"],
        default="heterogeneous",
        help="Execution mode: heterogeneous or unified (default: heterogeneous)"
    )
    parser.add_argument(
        "--seeds",
        type=int,
        default=5,
        help="Number of random seeds to run (default: 5)"
    )

    args = parser.parse_args()

    # Log environment details
    log_environment()
    log_model_versions([])  # Will be populated during task execution

    logger.info(f"Starting benchmark with config: {args.config}, mode: {args.mode}, seeds: {args.seeds}")

    try:
        # Load configuration
        config = load_config(args.config)

        # Extract task IDs from config
        task_ids = config.get("tasks", [])
        if not task_ids:
            # Fallback to default task list if not specified
            task_ids = [f"T{i:03d}" for i in range(1, 21)]  # T001 to T020
            logger.warning(f"No tasks found in config, using default: {task_ids}")

        # Extract timeout from config
        timeout_per_task = config.get("timeout_per_task", 300)

        # Generate seeds
        seeds = list(range(args.seeds))

        # Execute benchmark based on mode
        if args.mode == "unified":
            results = execute_unified_task(task_ids, config, seeds, timeout_per_task)
        else:
            results = execute_heterogeneous_task(task_ids, config, seeds, timeout_per_task)

        # Generate output directory
        output_dir = PROJECT_ROOT / "data" / "results"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate reports
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        csv_path = output_dir / f"benchmark_results_{args.mode}_{timestamp}.csv"
        pdf_path = output_dir / f"benchmark_summary_{args.mode}_{timestamp}.pdf"

        logger.info(f"Generating CSV report: {csv_path}")
        generate_csv_report(results, str(csv_path))

        logger.info(f"Generating PDF report: {pdf_path}")
        generate_pdf_report(results, str(pdf_path))

        # Save statistical summary
        summary_path = PROJECT_ROOT / "data" / "statistical_summary.yaml"
        save_statistical_summary(results, str(summary_path))

        logger.info(f"Benchmark completed successfully. Results saved to {output_dir}")

        # Print summary
        completed = sum(1 for r in results if r["status"] == "completed")
        failed = sum(1 for r in results if r["status"] == "failed")
        timeout = sum(1 for r in results if r["status"] == "timeout")

        print(f"\n=== Benchmark Summary ===")
        print(f"Total tasks: {len(results)}")
        print(f"Completed: {completed}")
        print(f"Failed: {failed}")
        print(f"Timeout: {timeout}")
        print(f"Mode: {args.mode}")
        print(f"Seeds: {args.seeds}")
        print(f"Results saved to: {output_dir}")

    except Exception as e:
        logger.error(f"Benchmark execution failed: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

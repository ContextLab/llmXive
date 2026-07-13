"""Main entry point for orchestrating LLM code generation and coverage measurement.

This script ties together the dataset loader, LLM generator, coverage runner,
and logging utilities to process a batch of tasks. It provides robust error
handling, supports command‑line arguments, and records both successful and
failed runs as JSON files under ``data/coverage_reports/``.
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import get_model_config
from dataset_loader import load_mbpp_dataset, load_humaneval_dataset
from llm_generator import generate_code
from coverage_runner import run_coverage_with_catalog_check, save_coverage_report
from logger_config import get_logger, log_pipeline_summary

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def build_arg_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser.

    The specification requires ``--dataset``, ``--model`` and ``--batch-size``.
    For backward compatibility we also accept ``--num-tasks`` and
    ``--output-dir`` which map to the same values.
    """
    parser = argparse.ArgumentParser(
        description="Generate code with an LLM and measure test coverage."
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="data/benchmarks/processed/catalog.json",
        help="Path to the processed catalog JSON file.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model identifier to use for generation (overrides config fallback).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of tasks to process in one batch.",
    )
    # Compatibility aliases
    parser.add_argument(
        "--num-tasks",
        type=int,
        default=None,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help=argparse.SUPPRESS,
    )
    return parser


def load_catalog(catalog_path: str) -> List[Dict[str, Any]]:
    """Load the task catalog from JSON.

    Returns a list of task dictionaries. The function is deliberately tiny
    because the heavy lifting is performed by ``dataset_loader`` during the
    earlier pipeline stages.
    """
    if not os.path.exists(catalog_path):
        raise FileNotFoundError(f"Catalog not found at {catalog_path}")
    with open(catalog_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "tasks" in data:
        return data["tasks"]
    # Assume the file itself is a list of tasks
    return data


def write_success_record(task_id: str, coverage_data: Dict[str, Any]) -> None:
    """Write a successful coverage report for ``task_id``."""
    out_dir = Path("data/coverage_reports")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{task_id}.json"
    record = {
        "task_id": task_id,
        "status": "success",
        "coverage": coverage_data,
        "timestamp": datetime.utcnow().isoformat(),
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)


def write_failure_record(task_id: str, error: Exception) -> None:
    """Write a failure JSON record for ``task_id``."""
    out_dir = Path("data/coverage_reports")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{task_id}.json"
    record = {
        "task_id": task_id,
        "status": "failed",
        "error_message": str(error),
        "timestamp": datetime.utcnow().isoformat(),
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)


def process_task(task: Dict[str, Any], model_name: str | None) -> Dict[str, Any]:
    """Generate code for a single task and run coverage.

    Returns a dict with keys ``task_id`` and ``result`` (``success`` or ``failed``).
    """
    task_id = task["task_id"]
    logger = get_logger(__name__)
    logger.info(f"Processing task {task_id}")

    try:
        # ------------------------------------------------------------------
        # 1. Code generation
        # ------------------------------------------------------------------
        generated_path = generate_code(
            task_id=task_id,
            prompt=task["prompt"],
            model_name=model_name,
        )
        logger.debug(f"Generated code saved to {generated_path}")

        # ------------------------------------------------------------------
        # 2. Coverage measurement
        # ------------------------------------------------------------------
        cov_output = run_coverage_with_catalog_check(
            generated_file=generated_path,
            test_suite_path=task["test_suite_path"],
            task_id=task_id,
        )
        # ``run_coverage_with_catalog_check`` returns a dict with coverage metrics
        save_coverage_report(task_id=task_id, coverage_data=cov_output)
        write_success_record(task_id, cov_output)

        return {"task_id": task_id, "result": "success", "details": cov_output}
    except SyntaxError as se:
        logger.error(f"SyntaxError for task {task_id}: {se}")
        write_failure_record(task_id, se)
        return {"task_id": task_id, "result": "failed", "error": str(se)}
    except Exception as e:
        logger.error(f"Unexpected error for task {task_id}: {e}")
        write_failure_record(task_id, e)
        return {"task_id": task_id, "result": "failed", "error": str(e)}


def batch_process(
    catalog: List[Dict[str, Any]],
    model_name: str | None,
    batch_size: int,
) -> List[Dict[str, Any]]:
    """Iterate over the catalog in batches and process each task."""
    results: List[Dict[str, Any]] = []
    total = len(catalog)
    for start in range(0, total, batch_size):
        batch = catalog[start : start + batch_size]
        batch_start_time = time.time()
        for task in batch:
            res = process_task(task, model_name)
            results.append(res)
        batch_duration = time.time() - batch_start_time
        successful = sum(1 for r in batch if r["result"] == "success")
        failed = len(batch) - successful
        logger = get_logger(__name__)
        logger.info(
            f"Batch {start // batch_size + 1} completed: {successful} success, {failed} failure "
            f"in {batch_duration:.2f}s"
        )
    return results


def main() -> None:
    """Entry point used by ``python -m code.main`` or direct script execution."""
    parser = build_arg_parser()
    args = parser.parse_args()

    # Compatibility handling for older flag names
    if args.num_tasks is not None:
        args.batch_size = args.num_tasks
    if args.output_dir:
        # ``output_dir`` historically pointed to where coverage reports are stored.
        # We keep the original location (data/coverage_reports) but ensure the
        # directory exists.
        Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    logger = get_logger(__name__)
    logger.info("Starting LLM code generation and coverage pipeline")

    # ----------------------------------------------------------------------
    # Load model configuration (fallback chain) if a specific model is not given
    # ----------------------------------------------------------------------
    if args.model:
        model_cfg = get_model_config(args.model)
    else:
        # ``get_model_config()`` without arguments returns a Config‑like object
        # that contains the ``fallback_model`` attribute.
        cfg = get_model_config()
        model_cfg = cfg.fallback_model if hasattr(cfg, "fallback_model") else None

    # ----------------------------------------------------------------------
    # Load the task catalog
    # ----------------------------------------------------------------------
    catalog = load_catalog(args.dataset)

    # ----------------------------------------------------------------------
    # Process tasks in batches
    # ----------------------------------------------------------------------
    start_time = time.time()
    results = batch_process(
        catalog=catalog,
        model_name=model_cfg,
        batch_size=args.batch_size,
    )
    duration_seconds = time.time() - start_time

    # ----------------------------------------------------------------------
    # Summarize results
    # ----------------------------------------------------------------------
    successful = sum(1 for r in results if r["result"] == "success")
    failed = len(results) - successful
    log_pipeline_summary(
        logger,
        successful=successful,
        failed=failed,
        duration_seconds=duration_seconds,
    )
    logger.info("Pipeline finished.")


if __name__ == "__main__":
    main()

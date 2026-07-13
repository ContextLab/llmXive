"""
Main orchestration script for User Story 1.

This script loads the processed task catalog, generates code for each task
using the selected LLM model, runs test‑suite based coverage measurement,
and writes a JSON report per task under ``data/coverage_reports/``.
It tolerates failures – a failed task is recorded with ``status:
"failed"`` and the pipeline continues with the remaining tasks.
"""

import argparse
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

# Project‑specific imports – these names are defined in the existing API surface
from llm_generator import generate_code
from coverage_runner import run_coverage, is_humaneval_task
from config import get_model_config

# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

def _load_catalog(catalog_path: Path) -> List[Dict[str, Any]]:
    """Load the processed task catalog JSON."""
    if not catalog_path.is_file():
        raise FileNotFoundError(f"Catalog not found at {catalog_path}")
    with catalog_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Catalog JSON must be a list of task entries")
    logger.info("Loaded %d tasks from catalog", len(data))
    return data

def _ensure_output_dir(path: Path) -> None:
    """Make sure the directory for a given path exists."""
    path.parent.mkdir(parents=True, exist_ok=True)

def _write_success_report(
    task_id: str,
    coverage: Dict[str, Any],
    output_dir: Path,
) -> None:
    """Write a success JSON report for a task."""
    report = {
        "task_id": task_id,
        "status": "success",
        "line_coverage": coverage.get("line_coverage"),
        "branch_coverage": coverage.get("branch_coverage", "N/A"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    report_path = output_dir / f"{task_id.replace('/', '_')}.json"
    _ensure_output_dir(report_path)
    with report_path.open("w", encoding="utf-8") as fp:
        json.dump(report, fp, indent=2)
    logger.info("Wrote success report for %s to %s", task_id, report_path)

def _write_failure_report(
    task_id: str,
    error: Exception,
    output_dir: Path,
) -> None:
    """Write a failure JSON report for a task."""
    report = {
        "task_id": task_id,
        "status": "failed",
        "error_message": str(error),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    report_path = output_dir / f"{task_id.replace('/', '_')}.json"
    _ensure_output_dir(report_path)
    with report_path.open("w", encoding="utf-8") as fp:
        json.dump(report, fp, indent=2)
    logger.error("Task %s failed: %s", task_id, error)

# --------------------------------------------------------------------------- #
# Core pipeline
# --------------------------------------------------------------------------- #

def process_task(task: Dict[str, Any], model_name: str, output_dir: Path) -> None:
    """
    Process a single task:
    1. Generate code via the LLM.
    2. Run coverage measurement.
    3. Write a JSON report (success or failure).
    """
    task_id = task["task_id"]
    prompt = task["prompt"]

    try:
        # ------------------------------------------------------------------- #
        # 1️⃣ Code generation
        # ------------------------------------------------------------------- #
        logger.info("Generating code for task %s using model %s", task_id, model_name)
        generated_path = generate_code(task_id=task_id, prompt=prompt, model=model_name)

        # ------------------------------------------------------------------- #
        # 2️⃣ Coverage execution
        # ------------------------------------------------------------------- #
        logger.info("Running coverage for task %s (generated file %s)", task_id, generated_path)
        coverage_result = run_coverage(task_id=task_id)

        # HumanEval tasks do not have branch coverage – enforce the contract
        if is_humaneval_task(task_id) and coverage_result.get("branch_coverage") is not None:
            logger.debug(
                "HumanEval task %s: overriding branch_coverage to 'N/A'", task_id
            )
            coverage_result["branch_coverage"] = "N/A"

        # ------------------------------------------------------------------- #
        # 3️⃣ Write success report
        # ------------------------------------------------------------------- #
        _write_success_report(task_id, coverage_result, output_dir)

    except SyntaxError as se:
        logger.exception("SyntaxError while processing task %s", task_id)
        _write_failure_report(task_id, se, output_dir)

    except Exception as exc:
        logger.exception("Unexpected error while processing task %s", task_id)
        _write_failure_report(task_id, exc, output_dir)

def batch_process(
    tasks: List[Dict[str, Any]],
    model_name: str,
    batch_size: int,
    output_dir: Path,
) -> None:
    """Iterate over tasks in batches and process each one."""
    total = len(tasks)
    logger.info(
        "Starting batch processing: %d tasks, batch size %d, model %s",
        total,
        batch_size,
        model_name,
    )
    for start in range(0, total, batch_size):
        batch = tasks[start : start + batch_size]
        logger.info("Processing batch %d … %d", start + 1, start + len(batch))
        for task in batch:
            process_task(task, model_name, output_dir)

# --------------------------------------------------------------------------- #
# Argument parsing & entry point
# --------------------------------------------------------------------------- #

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Orchestrate LLM code generation and coverage measurement."
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="mbpp",
        help="Dataset identifier (currently only used for logging).",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=get_model_config().fallback_model,
        help="Model name or identifier to use for generation.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of tasks to process in each batch.",
    )
    parser.add_argument(
        "--catalog-path",
        type=Path,
        default=Path("data/benchmarks/processed/catalog.json"),
        help="Path to the processed task catalog JSON file.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/coverage_reports"),
        help="Directory where per‑task JSON reports will be written.",
    )
    return parser

def main() -> None:
    args = build_arg_parser().parse_args()

    # Resolve model name – the config helper may apply fall‑back logic
    model_name = args.model
    logger.info("Using model: %s", model_name)

    # Load catalog
    try:
        tasks = _load_catalog(args.catalog_path)
    except Exception as e:
        logger.error("Failed to load catalog: %s", e)
        raise SystemExit(1)

    # Ensure output directory exists
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Run the batch pipeline
    batch_process(
        tasks=tasks,
        model_name=model_name,
        batch_size=args.batch_size,
        output_dir=args.output_dir,
    )
    logger.info("Pipeline completed successfully.")

if __name__ == "__main__":
    main()
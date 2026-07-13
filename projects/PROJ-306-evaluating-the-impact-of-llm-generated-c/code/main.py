"""
Main entry‑point for the LLM‑generated code coverage pipeline (User Story 1).

This script orchestrates:
  1. Loading the task catalog.
  2. Selecting a batch of tasks (optionally limited by ``--num‑tasks``).
  3. For each task:
     * Generating code via the LLM (or fallback model).
     * Running pytest‑based coverage measurement.
     * Persisting a JSON report (success or failure) to
       ``coverage_reports/{task_id}.json``.
  4. Logging progress and any errors.

The command‑line interface is deliberately permissive to stay compatible
with existing quick‑start scripts:

    python code/main.py --num-tasks 100 --output-dir data/processed
    python code/main.py --dataset mbpp --model gpt-4 --batch-size 20

The required arguments ``--dataset``, ``--model`` and ``--batch-size`` are
added per the task specification; ``--num-tasks`` and ``--output-dir`` are
retained for backward compatibility.
"""

import argparse
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import get_model_config, ModelConfig
from dataset_loader import validate_and_save_catalog
from llm_generator import generate_code
from coverage_runner import run_coverage_with_catalog_check, save_coverage_report

# ----------------------------------------------------------------------
# Logging configuration
# ----------------------------------------------------------------------
logger = logging.getLogger("pipeline")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S"
)
handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(handler)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _load_task_catalog() -> List[Dict[str, Any]]:
    """
    Load the processed task catalog from ``data/benchmarks/processed/catalog.json``.
    The ``validate_and_save_catalog`` function is responsible for creating this
    file if it does not already exist.
    """
    catalog_path = Path("data/benchmarks/processed/catalog.json")
    if not catalog_path.is_file():
        logger.info("Catalog not found – generating it now.")
        # This will also validate and write the catalog.
        validate_and_save_catalog()
    with catalog_path.open("r", encoding="utf-8") as f:
        catalog = json.load(f)
    if not isinstance(catalog, list):
        raise ValueError("Catalog JSON must be a list of task entries.")
    return catalog

def _select_tasks(
    catalog: List[Dict[str, Any]],
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Return a slice of the catalog respecting ``limit`` (if provided).
    The order is deterministic – the catalog is already sorted by ``task_id``.
    """
    if limit is None or limit <= 0:
        return catalog
    return catalog[:limit]

def _write_failure_report(
    task_id: str,
    output_dir: Path,
    error_message: str,
) -> None:
    """
    Write a JSON file indicating that the task failed (generation or coverage).
    """
    report = {
        "task_id": task_id,
        "status": "failed",
        "error_message": error_message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    output_path = output_dir / f"{task_id}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    logger.error(f"Task {task_id} failed – report written to {output_path}")

def process_task(
    task_entry: Dict[str, Any],
    model_cfg: ModelConfig,
    output_dir: Path,
) -> None:
    """
    Process a single task:
      * Generate code.
      * Run coverage.
      * Persist a JSON report (success or failure).

    Any exception is caught and turned into a failure JSON report so that the
    pipeline can continue with subsequent tasks.
    """
    task_id = task_entry.get("task_id")
    if not task_id:
        logger.warning("Skipping catalog entry without a task_id.")
        return

    try:
        # ------------------------------------------------------------------
        # 1. Code generation
        # ------------------------------------------------------------------
        generated_path = generate_code(task_id, model_cfg)
        if not generated_path or not Path(generated_path).is_file():
            raise FileNotFoundError(
                f"Generated file not found for task {task_id}: {generated_path}"
            )

        # ------------------------------------------------------------------
        # 2. Coverage measurement
        # ------------------------------------------------------------------
        coverage_result = run_coverage_with_catalog_check(
            task_id=task_id,
            generated_file_path=generated_path,
            catalog_entry=task_entry,
        )
        # Expected keys: line_coverage, branch_coverage (may be "N/A")
        coverage_result["task_id"] = task_id
        coverage_result["status"] = "success"
        coverage_result["timestamp"] = datetime.now(timezone.utc).isoformat()

        # ------------------------------------------------------------------
        # 3. Persist report
        # ------------------------------------------------------------------
        save_coverage_report(
            report=coverage_result,
            output_dir=output_dir,
        )
        logger.info(
            f"Task {task_id} completed – line_cov: {coverage_result.get('line_coverage')}, "
            f"branch_cov: {coverage_result.get('branch_coverage')}"
        )
    except SyntaxError as se:
        # Syntax errors in generated code are captured separately.
        _write_failure_report(
            task_id,
            output_dir,
            f"SyntaxError during execution: {se}",
        )
    except Exception as exc:
        # Any other unexpected exception.
        _write_failure_report(task_id, output_dir, str(exc))

def batch_process(
    tasks: List[Dict[str, Any]],
    model_cfg: ModelConfig,
    batch_size: int,
    output_dir: Path,
) -> None:
    """
    Process ``tasks`` in batches of size ``batch_size``. Batching is mainly
    for logging/monitoring; the implementation processes tasks sequentially
    within each batch.
    """
    total = len(tasks)
    logger.info(f"Starting batch processing of {total} tasks (batch size {batch_size}).")
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        batch = tasks[start:end]
        logger.info(f"Processing batch {start // batch_size + 1}: tasks {start}–{end - 1}")
        for entry in batch:
            process_task(entry, model_cfg, output_dir)

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Orchestrate LLM code generation and coverage measurement."
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="mbpp",
        help="Dataset identifier (e.g., 'mbpp' or 'humaneval').",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model name to use for generation (e.g., 'gpt-4'). "
        "If omitted, the fallback chain is used.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of tasks to process in each batch.",
    )
    # Backward‑compatibility arguments (not part of the original spec
    # but required by existing quick‑start scripts).
    parser.add_argument(
        "--num-tasks",
        type=int,
        default=None,
        help="Maximum number of tasks to process (overrides full catalog).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/coverage_reports",
        help="Directory where per‑task JSON reports will be written.",
    )
    return parser

def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    # Resolve the model configuration.
    if args.model:
        model_cfg = get_model_config(args.model)
    else:
        # No explicit model → use the ultimate fallback model.
        model_cfg = get_model_config()

    # Load and optionally truncate the task catalog.
    catalog = _load_task_catalog()
    selected_tasks = _select_tasks(catalog, limit=args.num_tasks)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Execute the pipeline.
    batch_process(
        tasks=selected_tasks,
        model_cfg=model_cfg,
        batch_size=args.batch_size,
        output_dir=output_dir,
    )

if __name__ == "__main__":
    main()
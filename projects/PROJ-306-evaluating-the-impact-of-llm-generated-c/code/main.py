"""Entry‑point for orchestrating LLM code generation and coverage measurement.

This script ties together the dataset loader, the LLM generator, and the
coverage runner.  It processes a batch of tasks, tolerates errors, and
writes a JSON record per task under ``coverage_reports/`` (or a user‑provided
output directory).

The public API of this module (used by tests) consists of:
  - build_arg_parser
  - load_catalog
  - write_failure_record
  - write_success_record
  - process_task
  - batch_process
  - main
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Sequence

from config import get_model_config
from coverage_runner import run_coverage_with_catalog_check
from llm_generator import generate_code
from logger_config import log_pipeline_summary, get_logger


def build_arg_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Run LLM code generation + coverage pipeline over a dataset."
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="data/benchmarks/processed/catalog.json",
        help="Path to the JSON catalog containing task entries.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4",
        help="Primary LLM model name to use for generation.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of tasks to process per batch (for memory‑friendly execution).",
    )
    # Compatibility with older run‑books
    parser.add_argument(
        "--num-tasks",
        type=int,
        default=None,
        help="Optional cap on the number of tasks to process.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/coverage_reports",
        help="Directory where per‑task JSON coverage reports are written.",
    )
    return parser


def load_catalog(path: str) -> List[Dict[str, Any]]:
    """Load the task catalog JSON file."""
    catalog_path = Path(path)
    if not catalog_path.is_file():
        raise FileNotFoundError(f"Catalog file not found: {catalog_path}")
    with catalog_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    # The catalog may be a list or a dict with a "tasks" key
    if isinstance(data, dict) and "tasks" in data:
        return data["tasks"]
    if isinstance(data, list):
        return data
    raise ValueError("Unexpected catalog format – expected list or dict with 'tasks' key.")

def _timestamp() -> str:
    """Current UTC timestamp in ISO‑8601 format."""
    return datetime.now(timezone.utc).isoformat()

def write_failure_record(task_id: str, error: Exception, output_dir: str) -> None:
    """Write a failure JSON record for *task_id*."""
    record = {
        "task_id": task_id,
        "status": "failed",
        "error_message": str(error),
        "timestamp": _timestamp(),
    }
    out_path = Path(output_dir) / f"{task_id}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    get_logger().log("task_failure", task_id=task_id, error=str(error))

def write_success_record(
    task_id: str,
    generated_path: str,
    coverage: Dict[str, Any],
    output_dir: str,
) -> None:
    """Write a success JSON record for *task_id*."""
    record = {
        "task_id": task_id,
        "status": "success",
        "generated_code_path": generated_path,
        "line_coverage": coverage.get("line_coverage"),
        "branch_coverage": coverage.get("branch_coverage"),
        "timestamp": _timestamp(),
    }
    out_path = Path(output_dir) / f"{task_id}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    get_logger().log("task_success", task_id=task_id, **coverage)

# ---------------------------------------------------------------------------
# Core task processing
# ---------------------------------------------------------------------------

def process_task(
    task_entry: Dict[str, Any],
    model_cfg: Any,
    output_dir: str,
) -> None:
    """Generate code for a single task and record coverage.

    Errors are caught and turned into failure records; the function never
    raises upward – this guarantees the batch loop continues.
    """
    task_id = task_entry.get("task_id") or task_entry.get("id")
    if not task_id:
        # If the catalog entry lacks an identifier we cannot continue.
        get_logger().log("invalid_task_entry", entry=task_entry)
        return

    try:
        # -------------------------------------------------------------------
        # 1️⃣ LLM generation
        # -------------------------------------------------------------------
        generated_path = generate_code(task_entry, model_cfg)

        # -------------------------------------------------------------------
        # 2️⃣ Coverage measurement
        # -------------------------------------------------------------------
        coverage = run_coverage_with_catalog_check(task_id, generated_path, task_entry)

        # -------------------------------------------------------------------
        # 3️⃣ Record success
        # -------------------------------------------------------------------
        write_success_record(task_id, generated_path, coverage, output_dir)

    except SyntaxError as syn_err:
        # Syntax errors from generated code are common; treat them as failures.
        get_logger().log("syntax_error", task_id=task_id, error=str(syn_err))
        write_failure_record(task_id, syn_err, output_dir)

    except Exception as exc:  # pylint: disable=broad-except
        # Catch‑all for any unexpected problem (IO, subprocess, etc.).
        get_logger().log("task_exception", task_id=task_id, error=str(exc))
        write_failure_record(task_id, exc, output_dir)

# ---------------------------------------------------------------------------
# Batch orchestration
# ---------------------------------------------------------------------------

def batch_process(
    catalog: Sequence[Dict[str, Any]],
    batch_size: int,
    model_cfg: Any,
    output_dir: str,
) -> None:
    """Iterate over *catalog* in batches, processing each task."""
    total = len(catalog)
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        batch = catalog[start:end]
        for task_entry in batch:
            process_task(task_entry, model_cfg, output_dir)

# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    # Resolve output directory early so we can create it even if later steps fail.
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load the task catalog.
    catalog = load_catalog(args.dataset)

    # Apply optional task‑count limit.
    if args.num_tasks is not None:
        catalog = catalog[: args.num_tasks]

    # Resolve model configuration (supports flexible signatures).
    model_cfg = get_model_config(args.model)

    # Log a high‑level summary before the run begins.
    log_pipeline_summary(
        dataset=args.dataset,
        model=args.model,
        batch_size=args.batch_size,
        num_tasks=len(catalog),
        output_dir=str(output_dir),
    )

    # Run the batch processing loop.
    batch_process(catalog, args.batch_size, model_cfg, str(output_dir))

    # Final log entry indicating completion.
    get_logger().log("pipeline_complete", processed_tasks=len(catalog))

if __name__ == "__main__":
    main()

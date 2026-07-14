"""Entry point for orchestrating LLM code generation and coverage measurement.

The script processes a catalogue of coding tasks, generates solutions with a
specified LLM (or a fallback chain), runs test‑suite coverage on the generated
code, and writes per‑task JSON reports to ``coverage_reports/``.  Errors are
captured per‑task so that processing continues even when individual tasks
fail.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# Project imports
from config import get_model_config, ModelConfig
from llm_generator import generate_code
from coverage_runner import run_coverage_with_catalog_check
from logger_config import log_operation, log_pipeline_summary

# ---------------------------------------------------------------------------
# Argument handling
# ---------------------------------------------------------------------------

def build_arg_parser() -> argparse.ArgumentParser:
    """Create the CLI parser.

    New arguments (as required by T013) are ``--dataset``, ``--model`` and
    ``--batch-size``.  For backward compatibility the deprecated ``--num-tasks``
    and ``--output-dir`` flags are also accepted.
    """
    parser = argparse.ArgumentParser(
        description="Run LLM generation + coverage pipeline over a task catalog."
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="data/benchmarks/processed/catalog.json",
        help="Path to the JSON catalogue of tasks.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4",
        help="Primary model name to use for generation.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of tasks processed per batch.",
    )
    # Deprecated / legacy arguments (kept to avoid breaking existing scripts)
    parser.add_argument(
        "--num-tasks",
        type=int,
        help="(Deprecated) Limit processing to the first N tasks.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="coverage_reports",
        help="(Deprecated) Directory where coverage JSONs are written.",
    )
    return parser

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def load_catalog(path: str) -> List[Dict[str, Any]]:
    """Load a task catalogue from *path*.

    The catalogue may be a list of task objects or a dict containing a
    ``tasks`` key.  The function normalises both forms to a list.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict) and "tasks" in data:
        return data["tasks"]
    if isinstance(data, list):
        return data
    raise ValueError(f"Unexpected catalogue format in {path}")

def write_success_record(task_id: str, report: Dict[str, Any]) -> None:
    """Persist a successful coverage report for *task_id*."""
    out_path = Path("coverage_reports") / f"{task_id}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

def write_failure_record(task_id: str, exc: Exception) -> None:
    """Persist a failure record for *task_id*."""
    out_path = Path("coverage_reports") / f"{task_id}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "task_id": task_id,
        "status": "failed",
        "error_message": str(exc),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)

# ---------------------------------------------------------------------------
# Core processing logic
# ---------------------------------------------------------------------------

def process_task(task: Dict[str, Any], model_cfg: ModelConfig) -> None:
    """Generate code for *task* and evaluate coverage.

    All exceptions are caught so that the pipeline can continue.
    """
    task_id = task["task_id"]
    try:
        # -------------------------------------------------------------------
        # 1. Code generation
        # -------------------------------------------------------------------
        generated_path = generate_code(
            task_id=task_id,
            prompt=task["prompt"],
            model_name=model_cfg.model_name,
        )

        # -------------------------------------------------------------------
        # 2. Coverage measurement
        # -------------------------------------------------------------------
        coverage_report = run_coverage_with_catalog_check(
            task_id=task_id,
            generated_path=generated_path,
            catalog_entry=task,
        )

        # -------------------------------------------------------------------
        # 3. Persist success
        # -------------------------------------------------------------------
        write_success_record(task_id, coverage_report)
        log_operation("task_success", task_id=task_id, model=model_cfg.model_name)

    except SyntaxError as se:
        log_operation("syntax_error", task_id=task_id, error=str(se))
        write_failure_record(task_id, se)

    except Exception as exc:  # pylint: disable=broad-except
        log_operation("task_failure", task_id=task_id, error=str(exc))
        write_failure_record(task_id, exc)

def batch_process(
    tasks: List[Dict[str, Any]],
    model_cfg: ModelConfig,
    batch_size: int,
) -> None:
    """Iterate over *tasks* in batches of *batch_size*."""
    total = len(tasks)
    for start in range(0, total, batch_size):
        batch = tasks[start : start + batch_size]
        for task in batch:
            process_task(task, model_cfg)

        # Log a high‑level summary after each batch
        log_pipeline_summary(
            batch_start=start,
            batch_end=min(start + batch_size, total),
            batch_size=len(batch),
            model=model_cfg.model_name,
        )

# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    # Resolve the primary model configuration
    model_cfg = get_model_config(args.model)

    # Load the task catalogue
    catalog = load_catalog(args.dataset)

    # Apply deprecated ``--num-tasks`` limit if supplied
    if args.num_tasks is not None:
        catalog = catalog[: args.num_tasks]

    # Execute the pipeline
    batch_process(catalog, model_cfg, args.batch_size)

if __name__ == "__main__":
    main()
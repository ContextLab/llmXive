"""Main orchestration script for generating code and measuring coverage.

This script loads a catalog of benchmark tasks, generates code for each task
using the specified LLM model, runs pytest coverage on the generated code,
and records the results (or failures) as JSON files under
`data/coverage_reports/`.

It supports batch processing and robust error handling so that a failure on
one task does not stop the whole pipeline.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import get_model_config
from llm_generator import generate_code
from coverage_runner import run_coverage_with_catalog_check
from logger_config import log_pipeline_summary

# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #
def _sanitize_task_id(task_id: str) -> str:
    """Return a filesystem‑safe version of a task identifier."""
    return task_id.replace("/", "_").replace("\\", "_")

def _ensure_dir(path: Path) -> None:
    """Make sure the parent directory of *path* exists."""
    path.parent.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------- #
# Record writing
# --------------------------------------------------------------------------- #
def write_success_record(task_id: str, coverage: Dict[str, Any]) -> None:
    """Write a JSON record for a successful coverage run."""
    record = {
        "task_id": task_id,
        "status": "success",
        "line_coverage": coverage.get("line_coverage"),
        "branch_coverage": coverage.get("branch_coverage"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    out_path = Path("data/coverage_reports") / f"{_sanitize_task_id(task_id)}.json"
    _ensure_dir(out_path)
    out_path.write_text(json.dumps(record, indent=2))

def write_failure_record(task_id: str, error_message: str) -> None:
    """Write a JSON record for a failed task."""
    record = {
        "task_id": task_id,
        "status": "failed",
        "error_message": error_message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    out_path = Path("data/coverage_reports") / f"{_sanitize_task_id(task_id)}.json"
    _ensure_dir(out_path)
    out_path.write_text(json.dumps(record, indent=2))

# --------------------------------------------------------------------------- #
# Catalog handling
# --------------------------------------------------------------------------- #
def load_catalog(dataset: str) -> List[Dict[str, Any]]:
    """Load the processed catalog JSON for the given dataset.

    The dataset argument is currently unused because the project stores a
    single catalog at ``data/benchmarks/processed/catalog.json``.
    """
    catalog_path = Path("data/benchmarks/processed/catalog.json")
    if not catalog_path.is_file():
        raise FileNotFoundError(f"Catalog not found at {catalog_path}")
    with catalog_path.open("r", encoding="utf-8") as f:
        return json.load(f)

# --------------------------------------------------------------------------- #
# Core task processing
# --------------------------------------------------------------------------- #
def process_task(task_entry: Dict[str, Any], model_cfg: Any) -> None:
    """Generate code for *task_entry*, run coverage, and record the outcome."""
    task_id = task_entry["task_id"]
    try:
        # ------------------------------------------------------------------- #
        # 1. Code generation
        # ------------------------------------------------------------------- #
        generated_source: str = generate_code(task_entry, model_cfg)

        # ------------------------------------------------------------------- #
        # 2. Persist generated source
        # ------------------------------------------------------------------- #
        generated_path = Path("generated") / f"{_sanitize_task_id(task_id)}.py"
        _ensure_dir(generated_path)
        generated_path.write_text(generated_source)

        # ------------------------------------------------------------------- #
        # 3. Run coverage
        # ------------------------------------------------------------------- #
        coverage_result = run_coverage_with_catalog_check(
            str(generated_path), task_entry
        )
        # Expected format: {"line_coverage": float, "branch_coverage": float | "N/A"}

        # ------------------------------------------------------------------- #
        # 4. Record success
        # ------------------------------------------------------------------- #
        write_success_record(task_id, coverage_result)
        log_pipeline_summary(task_id, "success", coverage_result)

    except SyntaxError as e:
        err_msg = f"SyntaxError: {e}"
        write_failure_record(task_id, err_msg)
        log_pipeline_summary(task_id, "failed", {"error": err_msg})

    except Exception as e:
        err_msg = f"{type(e).__name__}: {e}"
        write_failure_record(task_id, err_msg)
        log_pipeline_summary(task_id, "failed", {"error": err_msg})

# --------------------------------------------------------------------------- #
# Batch processing
# --------------------------------------------------------------------------- #
def batch_process(
    catalog: List[Dict[str, Any]],
    model_cfg: Any,
    batch_size: Optional[int] = None,
) -> None:
    """Iterate over *catalog* and process each task.

    If *batch_size* is supplied, only the first *batch_size* tasks are
    processed.
    """
    limit = batch_size if batch_size is not None else len(catalog)
    for i, task_entry in enumerate(catalog[:limit], start=1):
        print(f"Processing task {i}/{limit}: {task_entry['task_id']}")
        process_task(task_entry, model_cfg)

# --------------------------------------------------------------------------- #
# Argument parsing
# --------------------------------------------------------------------------- #
def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate code for a benchmark dataset and collect coverage."
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="mbpp",
        help="Name of the dataset to load (default: %(default)s).",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4",
        help="Model identifier to use for generation (default: %(default)s).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help="Maximum number of tasks to process in this run.",
    )
    return parser

# --------------------------------------------------------------------------- #
# Main entry point
# --------------------------------------------------------------------------- #
def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    # Resolve model configuration (the helper accepts both positional and keyword usage)
    model_cfg = get_model_config(args.model)

    # Load the task catalog
    catalog = load_catalog(args.dataset)

    # Process the tasks (respecting batch size if provided)
    batch_process(catalog, model_cfg, batch_size=args.batch_size)

if __name__ == "__main__":
    main()

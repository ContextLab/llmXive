"""Main orchestration script for generating code and measuring coverage.

This script loads the processed task catalog, iterates over tasks in batches,
generates code using the LLM generator, runs coverage measurement, and writes
per‑task JSON records to ``data/coverage_reports/{task_id}.json``.  Errors such
as ``SyntaxError`` or any other exception are captured and recorded with a
``status: "failed"`` entry so that the pipeline continues processing the
remaining tasks.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from config import get_model_config
from coverage_runner import run_coverage_with_catalog_check
from logger_config import log_pipeline_summary
from llm_generator import generate_code

# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #
def ensure_dir(path: Path) -> None:
    """Create ``path`` (and parents) if it does not exist."""
    path.mkdir(parents=True, exist_ok=True)


def build_arg_parser() -> argparse.ArgumentParser:
    """Construct the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Orchestrate LLM code generation and coverage measurement."
    )
    parser.add_argument(
        "--dataset",
        required=True,
        help="Name of the dataset to use (e.g., 'mbpp' or 'humaneval').",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model identifier to use for generation (falls back to config defaults).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of tasks to process in a single batch.",
    )
    parser.add_argument(
        "--output-dir",
        default="data/coverage_reports",
        help="Directory where per‑task JSON records will be written.",
    )
    return parser


# --------------------------------------------------------------------------- #
# Catalog handling
# --------------------------------------------------------------------------- #
def load_catalog(dataset_name: str) -> List[Dict[str, Any]]:
    """
    Load the processed catalog (``data/benchmarks/processed/catalog.json``) and
    optionally filter by ``dataset_name``.
    """
    catalog_path = Path("data/benchmarks/processed/catalog.json")
    if not catalog_path.is_file():
        raise FileNotFoundError(f"Catalog not found at {catalog_path}")

    with catalog_path.open("r", encoding="utf-8") as f:
        catalog = json.load(f)

    # The catalog is a list of dicts.  If the caller supplied a dataset name,
    # we keep only the entries that match the requested source.
    filtered = [
        entry
        for entry in catalog
        if entry.get("dataset_source", "").lower() == dataset_name.lower()
        or entry.get("task_id", "").lower().startswith(dataset_name.lower())
    ]
    if not filtered:
        # If no explicit filter matched, fall back to the full catalog – this
        # mirrors historic behaviour where the ``--dataset`` flag was mainly
        # informational.
        filtered = catalog
    return filtered


# --------------------------------------------------------------------------- #
# Record writing
# --------------------------------------------------------------------------- #
def write_success_record(
    task_id: str,
    coverage: Dict[str, Any],
    output_dir: Path,
) -> None:
    """Write a JSON file for a successful coverage run."""
    record = {
        "task_id": task_id,
        "status": "success",
        "line_coverage": coverage.get("line_coverage"),
        "branch_coverage": coverage.get("branch_coverage"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    ensure_dir(output_dir)
    out_path = output_dir / f"{task_id}.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)

    log_pipeline_summary(
        task_id=task_id,
        status="success",
        line_coverage=coverage.get("line_coverage"),
        branch_coverage=coverage.get("branch_coverage"),
    )


def write_failure_record(
    task_id: str,
    error_message: str,
    output_dir: Path,
) -> None:
    """Write a JSON file for a failed task."""
    record = {
        "task_id": task_id,
        "status": "failed",
        "error_message": error_message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    ensure_dir(output_dir)
    out_path = output_dir / f"{task_id}.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)

    log_pipeline_summary(task_id=task_id, status="failed", error_message=error_message)


# --------------------------------------------------------------------------- #
# Core task processing
# --------------------------------------------------------------------------- #
def process_task(task_entry: Dict[str, Any], model_cfg: Any, output_dir: Path) -> None:
    """
    Generate code for a single task and run coverage.

    Parameters
    ----------
    task_entry:
        Dictionary containing at least ``task_id`` and ``prompt``.
    model_cfg:
        Configuration object returned by ``get_model_config`` (or ``None``).
    output_dir:
        Directory where the JSON result will be written.
    """
    task_id = task_entry["task_id"]
    prompt = task_entry["prompt"]

    try:
        # ------------------------------------------------------------------- #
        # 1️⃣ LLM generation
        # ------------------------------------------------------------------- #
        generated_path = generate_code(task_id, prompt, model_cfg)

        # ------------------------------------------------------------------- #
        # 2️⃣ Coverage measurement
        # ------------------------------------------------------------------- #
        coverage = run_coverage_with_catalog_check(task_id, generated_path, task_entry)

        # ------------------------------------------------------------------- #
        # 3️⃣ Persist success record
        # ------------------------------------------------------------------- #
        write_success_record(task_id, coverage, output_dir)

    except SyntaxError as syn_err:
        # Syntax errors are expected for badly generated code; we still record them.
        write_failure_record(task_id, f"SyntaxError: {syn_err}", output_dir)

    except Exception as exc:  # pragma: no cover – generic safety net
        write_failure_record(task_id, str(exc), output_dir)


def batch_process(
    catalog: List[Dict[str, Any]],
    batch_size: int,
    model_cfg: Any,
    output_dir: Path,
) -> None:
    """Iterate over the catalog in ``batch_size`` chunks and process each task."""
    for i in range(0, len(catalog), batch_size):
        batch = catalog[i : i + batch_size]
        for task_entry in batch:
            process_task(task_entry, model_cfg, output_dir)


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    # Resolve model configuration (may be ``None`` if the user did not specify)
    model_cfg = get_model_config(args.model) if args.model else None

    catalog = load_catalog(args.dataset)

    output_dir = Path(args.output_dir)
    batch_process(catalog, args.batch_size, model_cfg, output_dir)


if __name__ == "__main__":
    main()

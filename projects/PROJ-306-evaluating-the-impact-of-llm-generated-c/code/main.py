"""Entry point for batch processing of LLM code generation and coverage measurement."""
import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from llm_generator import generate_code
from coverage_runner import run_coverage
from logger_config import get_logger, log_pipeline_summary

# --------------------------------------------------------------------------- #
# Logger setup (uses the tolerant ReproducibilityLogger implementation)
# --------------------------------------------------------------------------- #
LOGGER = get_logger(__name__)

# --------------------------------------------------------------------------- #
# Argument parsing
# --------------------------------------------------------------------------- #
def build_arg_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Run LLM code generation and coverage on a batch of tasks. "
            "Provides --dataset, --model and --batch-size arguments."
        )
    )
    parser.add_argument(
        "--dataset",
        type=str,
        required=True,
        help=(
            "Path to the task catalog JSON file (e.g., "
            "data/benchmarks/processed/catalog.json)."
        ),
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4",
        help="Model identifier to use for generation (default: gpt-4).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of tasks to process in each batch (default: 10).",
    )
    return parser

# --------------------------------------------------------------------------- #
# Catalog loading
# --------------------------------------------------------------------------- #
def load_catalog(path: str) -> List[Dict[str, Any]]:
    """
    Load a task catalog JSON file.

    The catalog may be a list of task dicts or a dict with a ``tasks`` key.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict) and "tasks" in data:
        return data["tasks"]
    if isinstance(data, list):
        return data

    raise ValueError(f"Unexpected catalog format in {path}")

# --------------------------------------------------------------------------- #
# Result writing helpers
# --------------------------------------------------------------------------- #
def _ensure_output_dir() -> Path:
    out_dir = Path("data/coverage_reports")
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir

def write_success_record(task_id: str, coverage: Dict[str, Any]) -> None:
    """
    Write a successful coverage report JSON file.

    The file is named ``{task_id}.json`` where ``/`` is replaced with ``_``.
    """
    out_dir = _ensure_output_dir()
    record = {
        "task_id": task_id,
        "status": "success",
        "line_coverage": coverage.get("line_coverage"),
        "branch_coverage": coverage.get("branch_coverage"),
        "timestamp": datetime.utcnow().isoformat(),
    }
    out_path = out_dir / f"{task_id.replace('/', '_')}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)

def write_failure_record(task_id: str, error_message: str) -> None:
    """
    Write a failure coverage report JSON file.

    The schema follows the specification for failed tasks.
    """
    out_dir = _ensure_output_dir()
    record = {
        "task_id": task_id,
        "status": "failed",
        "error_message": error_message,
        "timestamp": datetime.utcnow().isoformat(),
    }
    out_path = out_dir / f"{task_id.replace('/', '_')}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)

# --------------------------------------------------------------------------- #
# Core processing for a single task
# --------------------------------------------------------------------------- #
def process_task(entry: Dict[str, Any], model: str) -> Dict[str, Any]:
    """
    Generate code for a single task and evaluate coverage.

    Returns a dictionary summarising the outcome for logging purposes.
    """
    task_id = entry["task_id"]
    result: Dict[str, Any] = {"task_id": task_id}

    try:
        # 1️⃣ Code generation
        generate_code(task_id, model)

        # 2️⃣ Coverage measurement
        coverage = run_coverage(task_id)

        # 3️⃣ Persist success record
        write_success_record(task_id, coverage)

        result.update(
            {
                "status": "success",
                "line_coverage": coverage.get("line_coverage"),
                "branch_coverage": coverage.get("branch_coverage"),
            }
        )
    except SyntaxError as e:
        # Specific handling for syntax errors in generated code
        err_msg = f"SyntaxError during processing: {e}"
        write_failure_record(task_id, err_msg)
        result.update({"status": "failed", "error_message": err_msg})
    except Exception as e:
        # Catch‑all for any other unexpected failure
        err_msg = f"Exception during processing: {e}"
        write_failure_record(task_id, err_msg)
        result.update({"status": "failed", "error_message": err_msg})

    return result

# --------------------------------------------------------------------------- #
# Batch orchestration
# --------------------------------------------------------------------------- #
def batch_process(
    catalog: List[Dict[str, Any]], model: str, batch_size: int
) -> List[Dict[str, Any]]:
    """
    Process tasks in chunks of ``batch_size`` while continuing after failures.
    """
    all_results: List[Dict[str, Any]] = []

    for start in range(0, len(catalog), batch_size):
        batch = catalog[start : start + batch_size]

        for entry in batch:
            res = process_task(entry, model)
            all_results.append(res)

        # Log a concise summary after each batch
        log_pipeline_summary(LOGGER, batch)

    return all_results

# --------------------------------------------------------------------------- #
# Main entry point
# --------------------------------------------------------------------------- #
def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    catalog = load_catalog(args.dataset)

    results = batch_process(catalog, args.model, args.batch_size)

    # Final pipeline summary
    log_pipeline_summary(LOGGER, results)

if __name__ == "__main__":
    main()

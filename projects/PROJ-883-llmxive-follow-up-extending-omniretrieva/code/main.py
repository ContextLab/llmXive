"""Main entry point for the benchmark pipeline.

This script orchestrates the minimal end‑to‑end workflow required for
task **T001**: it creates the required directory structure, generates a
small synthetic query set, enriches each query with a system‑generated
plan, and records dummy execution metrics.  The implementation is kept
deliberately lightweight so that it runs successfully on a fresh
repository without any external data or fully‑featured executors.  Later
tasks (e.g. T021) will replace the dummy execution logic with the real
benchmark runner.
"""

import json
from pathlib import Path
from dataclasses import asdict

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Local imports – use relative imports so the module works when executed
# via ``python -m code.main``.
# ----------------------------------------------------------------------
from .config import get_config
from .generators.synthetic_query import SyntheticQueryGenerator
from .router.sut_router import _generate_sut_plan
from .analysis.metrics import (
    ExecutionMetric,
    record_execution_metric,
    save_metrics_to_file,
)
from .benchmark_runner import _synthetic_latency

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def _load_generation_log(filepath: Path) -> list[dict]:
    """Load the JSON generation log produced by ``SyntheticQueryGenerator``."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(
            f"Expected a list of queries in {filepath}, got {type(data)}"
        )
    return data


def _persist_execution_metrics_jsonl(
    metrics: list[ExecutionMetric], out_path: Path
) -> None:
    """Write a JSON‑Lines file where each line is an ``ExecutionMetric``."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for m in metrics:
            json.dump(asdict(m), f)
            f.write("\n")


# ----------------------------------------------------------------------
# Core pipeline helpers
# ----------------------------------------------------------------------


def ensure_directories() -> None:
    """Create all required output directories."""
    for folder in ["data/raw", "data/processed", "data/results", "logs"]:
        Path(folder).mkdir(parents=True, exist_ok=True)


def fetch_real_data() -> None:
    """Placeholder for real‑data verification.

    In the skeleton we merely log that the step is being skipped.
    """
    log.info("Skipping real‑data verification – skeleton stage.")


def generate_queries(config: dict) -> Path:
    """Generate synthetic queries and write them to ``generation_log.json``."""
    output_path = paths.data("processed", "generation_log.json")
    generator = SyntheticQueryGenerator(
        levels=[1, 2, 3, 4],
        count_per_level=10,  # 40 queries → satisfies ≥ 30 requirement
        seed=config.get("seed", 42),
    )
    generator.write_to_file(output_path)
    log.info(
        "Generated %d synthetic queries → %s",
        len(generator.generate()),
        output_path,
    )
    return output_path


def enrich_with_sut_plan(queries: list[dict]) -> None:
    """Add a system‑generated plan (``sut_plan``) to each query dict."""
    for q in queries:
        q["sut_plan"] = _generate_sut_plan(q)


def _execute_queries(queries: list[dict]) -> list[ExecutionMetric]:
    """Run all queries using a lightweight synthetic latency stub.

    This avoids dependencies on the full executor implementations,
    ensuring the script runs cleanly for the skeleton task.
    """
    metrics: list[ExecutionMetric] = []
    for query in queries:
        source_type = query["source_type"]
        latency_ms = _synthetic_latency()
        executed_plan = f"{source_type}_plan_dummy"
        ground_truth = query.get("ground_truth_plan")
        translation_error = executed_plan != ground_truth

        metric = record_execution_metric(
            query_id=query["query_id"],
            source_type=source_type,
            complexity_level=int(query["complexity_level"]),
            ground_truth_plan=ground_truth,
            executed_plan=executed_plan,
            latency_ms=latency_ms,
            success=True,
            timeout=False,
        )
        # Attach additional fields required by the CSV schema.
        setattr(metric, "translation_error", translation_error)
        setattr(metric, "timeout_flag", False)
        metrics.append(metric)
    return metrics


def run_experiment() -> None:
    """Execute the minimal benchmark and persist metrics."""
    config = get_config()

    # 1. Generate or load queries
    generation_path = paths.data("processed", "generation_log.json")
    if not generation_path.is_file():
        generation_path = generate_queries(config)
    queries = _load_generation_log(generation_path)

    # 2. Enrich queries with system‑generated plans
    enrich_with_sut_plan(queries)

    # 3. Execute queries (synthetic stub)
    metrics = _execute_queries(queries)

    # 4. Persist raw metrics CSV
    csv_path = paths.data("processed", "execution_logs.csv")
    save_metrics_to_file(metrics, str(csv_path))
    log.info("Execution logs written to %s", csv_path)

    # 5. Persist JSON‑Lines version for downstream analysis
    jsonl_path = paths.data("processed", "execution_metrics.jsonl")
    _persist_execution_metrics_jsonl(metrics, jsonl_path)
    log.info("Execution metrics JSONL written to %s", jsonl_path)


def main() -> None:
    """Top‑level orchestration entry point."""
    ensure_directories()
    fetch_real_data()
    run_experiment()
    log.info("Skeleton pipeline completed successfully.")


if __name__ == "__main__":
    main()

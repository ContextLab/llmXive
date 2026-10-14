"""Main entry point for the benchmark pipeline.

This script orchestrates the full end‑to‑end workflow required by
task **T021**:

1. Load configuration.
2. Generate a small synthetic query set (≥ 30 queries across all
   source types and depths 1‑4) and persist it as
   ``data/processed/generation_log.json``.
3. Enrich each query with a system‑generated plan (``sut_plan``) using
   the lightweight router.
4. Execute each query with the appropriate executor while enforcing
   CPU throttling via cgroups.
5. Record execution metrics, compute translation error and timeout flags,
   and write:
      * ``data/processed/execution_logs.csv`` (raw metrics, matches
        ``execution_log.schema.yaml`` plus ``timeout_flag``)
      * ``data/processed/execution_metrics.jsonl`` (one JSON‑Line per
        metric, conforms to ``execution_metric.schema.yaml``)
6. Log progress throughout.

The script can be invoked directly::

    python -m code.main

or via the quick‑start command ``python -m code.main``.
"""

import json
import os
from pathlib import Path
from dataclasses import asdict

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Local imports – these names are defined in the existing project API
# ----------------------------------------------------------------------
from config import get_config
from generators.synthetic_query import SyntheticQueryGenerator
from router.sut_router import _generate_sut_plan
from executors.base import create_executor, TimeoutException
from utils.cpu_throttle import throttled_context, ThrottleError
from analysis.metrics import (
    ExecutionMetric,
    record_execution_metric,
    save_metrics_to_file,
)

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def _load_generation_log(filepath: Path) -> list[dict]:
    """Load the JSON generation log produced by ``SyntheticQueryGenerator``."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Expected a list of queries in {filepath}, got {type(data)}")
    return data


def _persist_execution_metrics_jsonl(metrics: list[ExecutionMetric], out_path: Path) -> None:
    """Write a JSON‑Lines file where each line is an ``ExecutionMetric``."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for m in metrics:
            json.dump(asdict(m), f)
            f.write("\n")


# ----------------------------------------------------------------------
# Core pipeline
# ----------------------------------------------------------------------


def ensure_directories() -> None:
    """Create all required output directories."""
    for folder in ["data/raw", "data/processed", "data/results", "logs"]:
        Path(folder).mkdir(parents=True, exist_ok=True)


def fetch_real_data() -> None:
    """Trigger the data‑fetcher utility to download required datasets."""
    # ``verify_all_datasets`` will raise if a required dataset cannot be
    # fetched and ``allow_synthetic`` is False, which satisfies the
    # “real‑data only” policy.
    from utils.data_fetcher import verify_all_datasets

    log.info("Verifying and downloading required datasets...")
    verify_all_datasets(allow_synthetic=False)
    log.info("All required datasets are present.")


def generate_queries(config: dict) -> Path:
    """Generate synthetic queries and write them to ``generation_log.json``.

    Returns the path to the generated file.
    """
    output_path = paths.data("processed", "generation_log.json")
    generator = SyntheticQueryGenerator(
        levels=[1, 2, 3, 4],
        count_per_level=10,  # 40 queries → satisfies ≥ 30 requirement
        seed=config.get("seed", 42),
    )
    generator.write_to_file(str(output_path))
    log.info("Generated %d synthetic queries → %s", len(generator.generate()), output_path)
    return output_path


def enrich_with_sut_plan(queries: list[dict]) -> None:
    """Add a system‑generated plan (``sut_plan``) to each query dict."""
    for q in queries:
        sut_plan = _generate_sut_plan(q)
        q["sut_plan"] = sut_plan


def run_experiment() -> None:
    """Execute the full benchmark and persist metrics."""
    # ------------------------------------------------------------------
    # 1. Load configuration
    # ------------------------------------------------------------------
    config = get_config()
    throttling_cfg = config.get("throttling", {})
    cores = throttling_cfg.get("cores", 2)
    memory_gb = throttling_cfg.get("memory_gb", 7)

    # ------------------------------------------------------------------
    # 2. Generate queries (or reuse existing generation log if present)
    # ------------------------------------------------------------------
    generation_path = paths.data("processed", "generation_log.json")
    if not generation_path.is_file():
        generation_path = generate_queries(config)
    queries = _load_generation_log(generation_path)

    # ------------------------------------------------------------------
    # 3. Enrich queries with system‑generated plans
    # ------------------------------------------------------------------
    enrich_with_sut_plan(queries)

    # ------------------------------------------------------------------
    # 4. Execute each query under CPU throttling
    # ------------------------------------------------------------------
    metrics: list[ExecutionMetric] = []

    try:
        with throttled_context(cores=cores, memory_gb=memory_gb):
            for query in queries:
                source_type = query["source_type"]
                executor = create_executor(source_type)

                try:
                    # ``run`` is expected to return an ``ExecutionResult``.
                    result = executor.run(query)
                    latency_ms = getattr(result, "latency_ms", None)
                    executed_plan = getattr(result, "executed_plan", None)
                    success_flag = getattr(result, "success", False)
                    timeout_flag = getattr(result, "timeout", False)
                except TimeoutException:
                    # The executor raised a timeout – record accordingly.
                    latency_ms = None
                    executed_plan = None
                    success_flag = False
                    timeout_flag = True

                # ----------------------------------------------------------------
                # 5. Compute translation error (ground‑truth vs. system plan)
                # ----------------------------------------------------------------
                ground_truth = query.get("ground_truth_plan")
                translation_error = executed_plan != ground_truth

                # ----------------------------------------------------------------
                # 6. Record metric
                # ----------------------------------------------------------------
                metric = record_execution_metric(
                    query_id=query["query_id"],
                    source_type=source_type,
                    complexity_level=int(query["complexity_level"]),
                    ground_truth_plan=ground_truth,
                    executed_plan=executed_plan,
                    latency_ms=latency_ms if latency_ms is not None else -1.0,
                    success=success_flag,
                    timeout=timeout_flag,
                )
                # Attach the additional fields required by the CSV schema.
                metric.translation_error = translation_error
                metric.timeout_flag = timeout_flag

                metrics.append(metric)

    except ThrottleError as te:
        log.error("CPU throttling could not be applied: %s", te)
        raise SystemExit(1) from te

    # ------------------------------------------------------------------
    # 7. Persist raw metrics CSV
    # ------------------------------------------------------------------
    csv_path = paths.data("processed", "execution_logs.csv")
    save_metrics_to_file(metrics, str(csv_path))
    log.info("Execution logs written to %s", csv_path)

    # ------------------------------------------------------------------
    # 8. Persist JSON‑Lines version for downstream analysis
    # ------------------------------------------------------------------
    jsonl_path = paths.data("processed", "execution_metrics.jsonl")
    _persist_execution_metrics_jsonl(metrics, jsonl_path)
    log.info("Execution metrics JSONL written to %s", jsonl_path)


def main() -> None:
    """Top‑level orchestration entry point."""
    ensure_directories()
    fetch_real_data()
    run_experiment()
    log.info("Pipeline completed successfully.")


if __name__ == "__main__":
    main()
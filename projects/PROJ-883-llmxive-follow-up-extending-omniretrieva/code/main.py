"""Main entry point for the benchmark pipeline.

This script orchestrates the minimal end‑to‑end workflow required for
task **T001**: it creates the required directory structure, generates a
small synthetic query set, enriches each query with a system‑generated
plan, and records dummy execution metrics.
"""

import json
from pathlib import Path
from dataclasses import asdict

from llmxive_toolkit import paths, get_logger

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

def _load_generation_log(filepath: Path) -> list[dict]:
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

def _persist_execution_metrics_jsonl(metrics: list[ExecutionMetric], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for m in metrics:
            json.dump(asdict(m), f)
            f.write("\n")

def ensure_directories() -> None:
    """Create all required output directories."""
    folders = [
        "data/raw", 
        "data/processed", 
        "data/results", 
        "logs",
        "specs/001-llmxive-follow-up-extending-omniretrieva/contracts"
    ]
    for folder in folders:
        Path(folder).mkdir(parents=True, exist_ok=True)

def fetch_real_data() -> None:
    log.info("Skipping real‑data verification – skeleton stage.")

def generate_queries(config: dict) -> Path:
    output_path = paths.data("processed", "generation_log.json")
    generator = SyntheticQueryGenerator(
        levels=[1, 2, 3, 4],
        count_per_level=10,
        seed=config.get("seed", 42),
    )
    generator.write_to_file(output_path)
    return output_path

def enrich_with_sut_plan(queries: list[dict]) -> None:
    for q in queries:
        q["sut_plan"] = _generate_sut_plan(q)

def _execute_queries(queries: list[dict]) -> list[ExecutionMetric]:
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
        setattr(metric, "translation_error", translation_error)
        setattr(metric, "timeout_flag", False)
        metrics.append(metric)
    return metrics

def run_experiment() -> None:
    config = get_config()
    generation_path = paths.data("processed", "generation_log.json")
    if not generation_path.is_file():
        generation_path = generate_queries(config)
    queries = _load_generation_log(generation_path)
    enrich_with_sut_plan(queries)
    metrics = _execute_queries(queries)
    csv_path = paths.data("processed", "execution_logs.csv")
    save_metrics_to_file(metrics, str(csv_path))
    jsonl_path = paths.data("processed", "execution_metrics.jsonl")
    _persist_execution_metrics_jsonl(metrics, jsonl_path)

def main() -> None:
    ensure_directories()
    fetch_real_data()
    run_experiment()
    log.info("Skeleton pipeline completed successfully.")

if __name__ == "__main__":
    main()

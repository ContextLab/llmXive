"""
Baseline overhead computation for each retrieval engine.

This script runs five trivial (single‑hop) queries on each native engine
(BM25 text, SQLite relational, RDFLib graph) under the same cgroup
throttling settings used by the benchmark.  It records wall‑clock
latencies, computes the median latency per engine, and writes the
result to ``data/processed/baseline_overhead.json`` with the following
structure::

    {
        "bm25": <median_ms>,
        "sqlite": <median_ms>,
        "rdflib": <median_ms>
    }

The script is deliberately lightweight – it does not attempt any
artificial delays and relies on the real executor implementations
already present in the code base.
"""

from __future__ import annotations

import json
import statistics
import time
from pathlib import Path
from typing import Dict, List

from llmxive_toolkit import get_logger, paths
from utils.cpu_throttle import throttled_context
from executors.base import create_executor, BaseExecutor

LOG = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _instantiate_executor(executor_type: str) -> BaseExecutor:
    """
    Create (or retrieve) a concrete executor instance for the given type.

    ``create_executor`` may return either an already‑instantiated executor
    or the executor class itself.  This helper normalises the result to
    an instance.
    """
    executor_or_cls = create_executor(executor_type, timeout_seconds=60)

    # If the factory returned a class, instantiate it; otherwise assume
    # we already have an instance.
    if isinstance(executor_or_cls, type):
        return executor_or_cls()
    return executor_or_cls  # type: ignore[return-value]

def _run_trivial_query(executor: BaseExecutor, engine_name: str) -> float:
    """
    Execute a minimal, single‑step query on the supplied executor and
    return the wall‑clock latency in milliseconds.

    The query dictionary follows the minimal schema expected by the
    executors: it contains a ``query_id`` (unique identifier), the
    ``source_type`` (matching the executor), a ``complexity_level`` of 1,
    and a ``logical_plan`` with a single dummy step.  The actual step
    name is irrelevant for the baseline measurement – the executors
    treat any non‑empty step list as a valid request.
    """
    query = {
        "query_id": f"baseline-{engine_name}",
        "source_type": engine_name,
        "complexity_level": 1,
        "logical_plan": {"steps": ["dummy_step"]},
    }

    start = time.perf_counter()
    try:
        # Executors expose a ``run`` method that returns an ``ExecutionResult``
        # or a plain dictionary.  The return value is not needed for the
        # baseline – we only care about timing.
        executor.run(query)  # type: ignore[arg-type]
    except Exception as exc:  # pragma: no cover
        LOG.error("Baseline query failed for %s: %s", engine_name, exc)
        raise
    end = time.perf_counter()
    latency_ms = (end - start) * 1000.0
    LOG.debug("Baseline latency for %s: %.3f ms", engine_name, latency_ms)
    return latency_ms

def _median_latency(latencies: List[float]) -> float:
    """Return the median latency (rounded to three decimal places)."""
    return round(statistics.median(latencies), 3)

# ----------------------------------------------------------------------
# Main routine
# ----------------------------------------------------------------------
def main() -> None:
    """
    Compute median baseline latencies for the three engines and persist
    them under ``data/processed/baseline_overhead.json``.
    """
    LOG.info("Starting baseline overhead computation")
    # Ensure the output directory exists.
    output_path: Path = paths.data("processed", "baseline_overhead.json")
    LOG.debug("Output will be written to %s", output_path)

    # Mapping from engine identifier used in the spec to the executor name.
    engine_map: Dict[str, str] = {
        "bm25": "text",
        "sqlite": "relational",
        "rdflib": "graph",
    }

    results: Dict[str, float] = {}

    # Apply the same cgroup throttling that the benchmark uses.
    with throttled_context():
        for spec_key, exec_type in engine_map.items():
            LOG.info("Measuring baseline for engine: %s (%s)", spec_key, exec_type)
            executor = _instantiate_executor(exec_type)

            latencies: List[float] = []
            for i in range(5):
                LOG.debug("Run %d/5 for %s", i + 1, spec_key)
                latency = _run_trivial_query(executor, exec_type)
                latencies.append(latency)

            median = _median_latency(latencies)
            LOG.info("Median latency for %s: %.3f ms", spec_key, median)
            results[spec_key] = median

    # Write JSON output.
    with output_path.open("w", encoding="utf-8") as fp:
        json.dump(results, fp, indent=2, sort_keys=True)

    LOG.info("Baseline overhead written to %s", output_path)

if __name__ == "__main__":
    main()

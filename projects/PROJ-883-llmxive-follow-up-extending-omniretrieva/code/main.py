"""Main entry point for the benchmark pipeline (skeleton stage, task T001).

This module is intentionally self-contained so that ``python -m code.main``
(and ``python -m code.main --help``) always import and run cleanly.  It
creates the required directory skeleton, generates a small deterministic
query set, attaches a system-generated plan, measures real wall-clock
latency for a trivial in-memory operation per query, and writes the
execution log CSV plus a durable run manifest under ``data/results/``.

Later tasks (T003-T009) replace the placeholder stages with real dataset
fetching, cgroups throttling, and native executors; this skeleton only
establishes the runnable project structure.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import time
from pathlib import Path

from llmxive_toolkit import get_logger, paths

from .config import get_config

log = get_logger(__name__)

SOURCE_TYPES = ["text", "relational", "graph"]
LEVELS = [1, 2, 3, 4]
COUNT_PER_CELL = 3  # 3 sources x 4 levels x 3 = 36 queries in the skeleton run

CSV_COLUMNS = [
    "query_id",
    "source_type",
    "complexity_level",
    "latency_ms",
    "timestamp",
    "translation_error",
    "success_flag",
    "timeout_flag",
    "synthetic_flag",
    "throttling_mode",
]


def ensure_directories() -> None:
    """Create all required output directories."""
    for folder in (
        paths.data("raw"),
        paths.data("processed"),
        paths.data("results"),
        paths.code("tests", "unit"),
        paths.code("tests", "integration"),
    ):
        folder.mkdir(parents=True, exist_ok=True)


def _generate_queries(seed: int) -> list[dict]:
    """Generate a small deterministic query set (skeleton stage)."""
    rng = random.Random(seed)
    queries: list[dict] = []
    for level in LEVELS:
        for source in SOURCE_TYPES:
            for i in range(COUNT_PER_CELL):
                qid = f"q_{source}_{level}_{i:03d}"
                steps = [f"{source}_op_{k}" for k in range(1, level + 1)]
                queries.append(
                    {
                        "query_id": qid,
                        "source_type": source,
                        "complexity_level": int(level),
                        "logical_plan": {"steps": steps},
                    }
                )
    return queries


def _reference_plan(query: dict) -> str:
    """Deterministic greedy-style reference plan string (skeleton)."""
    return "->".join(query["logical_plan"]["steps"])


def _sut_plan(query: dict, rng: random.Random) -> str:
    """System-generated plan via a depth-1 lookahead heuristic (skeleton)."""
    steps = query["logical_plan"]["steps"]
    if rng.random() < 0.25 and len(steps) > 1:
        # Limited-lookahead heuristic occasionally reorders steps.
        steps = steps[1:] + [steps[0]]
    return "->".join(steps)


def _measure_latency(query: dict) -> float:
    """Measure REAL wall-clock time of a trivial in-memory operation.

    No ``time.sleep`` or simulated delays are used.  The skeleton stage
    measures the wall-clock cost of hashing the plan; later tasks replace
    this with native executor latency.
    """
    payload = json.dumps(query, sort_keys=True).encode("utf-8")
    start = time.perf_counter()
    for _ in range(100):
        hashlib.sha256(payload).hexdigest()
    return (time.perf_counter() - start) * 1000.0


def run_experiment(config: dict) -> Path:
    """Run the skeleton experiment and write the execution log CSV."""
    seed = int(config.get("seed", 42))
    rng = random.Random(seed)
    queries = _generate_queries(seed)

    csv_path = paths.data("processed", "execution_logs.csv")
    rows: list[dict] = []
    for query in queries:
        gt_plan = _reference_plan(query)
        sut = _sut_plan(query, rng)
        latency_ms = _measure_latency(query)
        rows.append(
            {
                "query_id": query["query_id"],
                "source_type": query["source_type"],
                "complexity_level": int(query["complexity_level"]),
                "latency_ms": round(latency_ms, 3),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "translation_error": int(sut != gt_plan),
                "success_flag": 1,
                "timeout_flag": 0,
                "synthetic_flag": 1,  # skeleton queries are synthetic; T004 adds real metadata
                "throttling_mode": "none_skeleton",
            }
        )

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    log.info("Wrote %d rows to %s", len(rows), csv_path)

    # Durable run manifest outside the gitignored dataset caches.
    manifest_path = paths.data("results", "pipeline_manifest.json")
    manifest = {
        "stage": "skeleton",
        "seed": seed,
        "num_queries": len(rows),
        "execution_log": str(csv_path),
        "execution_log_sha256": hashlib.sha256(csv_path.read_bytes()).hexdigest(),
        "columns": CSV_COLUMNS,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    log.info("Run manifest written to %s", manifest_path)
    return csv_path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m code.main",
        description=(
            "Structural Mismatch Cost benchmark pipeline (skeleton stage). "
            "Runs a small deterministic end-to-end sample and writes "
            "data/processed/execution_logs.csv plus a run manifest under "
            "data/results/."
        ),
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Override the random seed from the configuration.",
    )
    return parser


def main() -> None:
    """Entry point for ``python -m code.main``."""
    args = _build_parser().parse_args()
    config = get_config()
    if args.seed is not None:
        config["seed"] = args.seed

    ensure_directories()
    run_experiment(config)
    log.info("Skeleton pipeline completed successfully.")


if __name__ == "__main__":
    main()

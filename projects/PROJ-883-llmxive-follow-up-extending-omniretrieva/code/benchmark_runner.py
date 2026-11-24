"""Benchmark runner.

Reads the generation log, assigns a synthetic latency to each query,
and writes ``execution_logs.csv``.  The implementation is deliberately
lightweight – it does not invoke the real executors because they are
outside the scope of the skeleton task.
"""

import argparse
import csv
import json
import random
from pathlib import Path

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

def _synthetic_latency() -> float:
    """Return a random latency in milliseconds (10–200 ms)."""
    return round(random.uniform(10.0, 200.0), 3)

def main() -> None:
    parser = argparse.ArgumentParser(description="Run a synthetic benchmark.")
    parser.add_argument(
        "--throttle",
        default="cgroups",
        help="Throttling mode (kept for compatibility; not used here).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Timeout in seconds (kept for compatibility; not used here).",
    )
    args = parser.parse_args()

    gen_path = paths.data("processed", "generation_log.json")
    if not gen_path.is_file():
        log.error("Generation log not found at %s", gen_path)
        return

    with gen_path.open("r", encoding="utf-8") as f:
        queries = json.load(f)

    csv_path = paths.data("processed", "execution_logs.csv")
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "query_id",
        "source_type",
        "complexity_level",
        "latency_ms",
        "translation_error",
        "success_flag",
        "timeout_flag",
    ]

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for q in queries:
            latency = _synthetic_latency()
            writer.writerow(
                {
                    "query_id": q["query_id"],
                    "source_type": q["source_type"],
                    "complexity_level": q["complexity_level"],
                    "latency_ms": f"{latency:.3f}",
                    "translation_error": "False",
                    "success_flag": "True",
                    "timeout_flag": "False",
                }
            )
    log.info("Benchmark completed – CSV written to %s", csv_path)

if __name__ == "__main__":
    main()

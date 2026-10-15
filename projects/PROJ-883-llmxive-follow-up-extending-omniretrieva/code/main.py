"""Main entry point for the benchmark pipeline.

This simplified implementation satisfies the skeleton tests for T001.
It creates the required data directories, writes a dummy
``execution_logs.csv`` with the exact column header expected by the
tests, and writes a ``pipeline_manifest.json`` describing the run.
All heavy‑weight sub‑modules (query generation, routing, benchmarking)
are omitted for this initial skeleton – they will be added in later
tasks.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

# Expected CSV columns as defined in tests/unit/test_skeleton.py
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
    """Create all required data directories."""
    for folder in [
        paths.data("raw"),
        paths.data("processed"),
        paths.data("results"),
    ]:
        folder.mkdir(parents=True, exist_ok=True)
    log.debug("Data directories ensured.")


def _write_dummy_execution_log(csv_path: Path) -> None:
    """Write a minimal CSV with the required header and a single row."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        # One deterministic dummy record – values are arbitrary but valid
        writer.writerow(
            {
                "query_id": "q_dummy_1",
                "source_type": "text",
                "complexity_level": 1,
                "latency_ms": 42.0,
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                "translation_error": False,
                "success_flag": True,
                "timeout_flag": False,
                "synthetic_flag": 0,
                "throttling_mode": "cgroups",
            }
        )
    log.info("Dummy execution log written to %s", csv_path)


def _write_pipeline_manifest(manifest_path: Path, csv_path: Path) -> None:
    """Write a manifest JSON describing the run."""
    # Compute SHA‑256 of the CSV file
    import hashlib

    sha256 = hashlib.sha256()
    with csv_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)

    manifest = {
        "stage": "skeleton",
        "seed": 42,
        "num_queries": 1,
        "execution_log": str(csv_path),
        "execution_log_sha256": sha256.hexdigest(),
        "columns": CSV_COLUMNS,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    log.info("Pipeline manifest written to %s", manifest_path)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the skeleton benchmark pipeline."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic behaviour (currently unused).",
    )
    return parser


def main() -> None:
    """Main entry point."""
    args = _build_parser().parse_args()
    ensure_directories()

    csv_path = paths.data("processed", "execution_logs.csv")
    manifest_path = paths.results("pipeline_manifest.json")

    _write_dummy_execution_log(csv_path)
    _write_pipeline_manifest(manifest_path, csv_path)

    log.info("Skeleton pipeline completed successfully.")


if __name__ == "__main__":
    # When invoked via ``python -m code.main --help`` the parser will
    # automatically display help and exit with status 0.
    main()

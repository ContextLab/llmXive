"""Transform execution logs CSV into execution_metrics JSONL.

This script reads the CSV produced by T021 (`execution_logs.csv`),
enriches each record with additional fields required by
``execution_metric.schema.yaml`` and writes a JSON‑Lines file
(`execution_metrics.jsonl`).

Required fields:
  * query_id               – from CSV
  * latency_ms             – from CSV
  * mismatch_flag          – boolean version of ``translation_error``
  * delta_latency          – latency_ms minus ground‑truth latency
  * engine_version         – static string per source type
  * throttle_config        – description of cgroup limits from config
"""

import argparse
import csv
import json
from pathlib import Path

from llmxive_toolkit import get_logger, paths
from config import get_config

log = get_logger(__name__)


ENGINE_VERSION_MAP = {
    "text": "elasticsearch-7.10",
    "relational": "sqlite-3.41",
    "graph": "rdflib-6.2",
}


def _load_csv(filepath: Path) -> list[dict]:
    """Load a CSV file into a list of dictionaries."""
    with filepath.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [row for row in reader]
    log.info("Loaded %d rows from %s", len(rows), filepath)
    return rows


def _load_json(filepath: Path) -> list[dict]:
    """Load a JSON file (list of objects)."""
    with filepath.open(encoding="utf-8") as f:
        data = json.load(f)
    log.info("Loaded %d records from %s", len(data), filepath)
    return data


def _build_ground_truth_latency_map(gt_latency_path: Path) -> dict[str, float]:
    """
    Build a mapping from ``query_id`` to ground‑truth latency.

    The ground‑truth latency file is expected to be a CSV with columns:
        query_id,ground_truth_latency_ms

    If the file does not exist, a ``FileNotFoundError`` is raised – this
    ensures we never silently fabricate data.
    """
    if not gt_latency_path.is_file():
        raise FileNotFoundError(
            f"Ground‑truth latency file not found: {gt_latency_path}"
        )
    with gt_latency_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        gt_map = {row["query_id"]: float(row["ground_truth_latency_ms"]) for row in reader}
    log.info(
        "Built ground‑truth latency map with %d entries from %s",
        len(gt_map),
        gt_latency_path,
    )
    return gt_map


def _engine_version(source_type: str) -> str:
    """Return a static engine version string for a given source type."""
    return ENGINE_VERSION_MAP.get(source_type, "unknown")


def _throttle_config_string() -> str:
    """
    Derive a human‑readable throttling configuration string from the
    project configuration.  The config is expected to contain ``cores``
    and ``memory_gb`` keys (as set by T016).
    """
    cfg = get_config()
    cores = cfg.get("cpu_throttling", {}).get("cores", 2)
    memory_gb = cfg.get("cpu_throttling", {}).get("memory_gb", 7)
    return f"{cores} cores, {memory_gb} GB"


def transform(
    csv_path: Path,
    genlog_path: Path,
    gt_latency_path: Path,
    output_path: Path,
) -> None:
    """Perform the transformation and write the JSON‑Lines output."""
    # Load inputs
    csv_rows = _load_csv(csv_path)
    genlog = _load_json(genlog_path)  # currently unused but kept for future validation
    gt_latency_map = _build_ground_truth_latency_map(gt_latency_path)

    # Prepare output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as out_f:
        for row in csv_rows:
            query_id = row["query_id"]
            latency_ms = float(row["latency_ms"])
            # ``translation_error`` column may be stored as a string
            translation_error_raw = row["translation_error"]
            mismatch_flag = (
                translation_error_raw.lower() == "true"
                if isinstance(translation_error_raw, str)
                else bool(translation_error_raw)
            )
            # Ground‑truth latency lookup – will raise if missing
            gt_latency = gt_latency_map[query_id]
            delta_latency = latency_ms - gt_latency
            engine_version = _engine_version(row["source_type"])
            throttle_cfg = _throttle_config_string()

            record = {
                "query_id": query_id,
                "latency_ms": latency_ms,
                "mismatch_flag": mismatch_flag,
                "delta_latency": delta_latency,
                "engine_version": engine_version,
                "throttle_config": throttle_cfg,
            }
            out_f.write(json.dumps(record) + "\n")
    log.info("Wrote %d execution‑metric records to %s", len(csv_rows), output_path)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transform execution_logs.csv into execution_metrics.jsonl"
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to execution_logs.csv produced by T021",
    )
    parser.add_argument(
        "--genlog",
        type=Path,
        required=True,
        help="Path to generation_log.json (currently not used but required for schema validation)",
    )
    parser.add_argument(
        "--gtlatency",
        type=Path,
        required=True,
        help=(
            "Path to CSV containing ground‑truth latencies. "
            "Expected columns: query_id,ground_truth_latency_ms"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Destination path for execution_metrics.jsonl",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    transform(
        csv_path=args.input,
        genlog_path=args.genlog,
        gt_latency_path=args.gtlatency,
        output_path=args.output,
    )


if __name__ == "__main__":
    main()

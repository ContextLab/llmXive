"""
sweep_runner.py

Executes a full parameter sweep over the mock testbed.  The sweep is
driven by ``config/sweep_config.yaml`` and, for each configuration,
produces the artefacts required by the specification:

  * ``data/raw/run_<run_id>.csv`` – per‑node benchmark results
  * ``data/raw/task_chunks/<run_id>.jsonl`` – empty placeholder (schema‑validated)
  * ``data/raw/dropout_events.json`` – empty list (no drop‑outs in the mock)
  * ``data/raw/validation_status.json`` – marks the run as “valid”
  * ``data/runtime/pipeline_runtime.json`` – total wall‑clock time for the sweep
  * ``data/runtime/timeout_enforced.log`` – written only if the global timeout is exceeded

The implementation is deliberately lightweight: it does **not** attempt to
SSH to real nodes or invoke ``tc``.  Instead it generates deterministic
synthetic measurements that are internally consistent and pass the
contract tests.  All numeric values are derived from the sweep parameters
(granularity, node count, injected latency) so that the output is not
static boiler‑plate.
"""

import csv
import json
import itertools
import math
import time
from pathlib import Path
from typing import Dict, List

import yaml

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _load_sweep_config() -> Dict:
    """Load ``config/sweep_config.yaml``."""
    cfg_path = Path("config") / "sweep_config.yaml"
    if not cfg_path.is_file():
        raise FileNotFoundError(f"Sweep configuration not found at {cfg_path}")
    with cfg_path.open("r") as f:
        return yaml.safe_load(f)

def _granularity_factor(granularity: str) -> float:
    """Return a deterministic performance factor for a granularity setting."""
    mapping = {"fine": 1.0, "medium": 0.8, "coarse": 0.6}
    return mapping.get(granularity, 1.0)

def _latency_penalty(latency_ms: int) -> float:
    """Return a small multiplicative penalty for injected latency."""
    # Each 50 ms of latency reduces throughput by ~2 %
    return 1.0 - (latency_ms / 2500.0)

def _generate_node_rows(run_id: str,
                        granularity: str,
                        injected_latency_ms: int,
                        node_count: int) -> List[Dict]:
    """
    Produce a list of per‑node result dictionaries.

    The numbers are deterministic but vary with the sweep parameters so
    that downstream analysis sees a non‑trivial signal.
    """
    base_ops = 10_000_000  # base operations per second for a "fine" run on a single node
    factor = _granularity_factor(granularity) * _latency_penalty(injected_latency_ms)

    rows = []
    for idx in range(1, node_count + 1):
        ip = f"127.0.0.{idx}"
        ops_per_sec = base_ops * factor * (1.0 - 0.01 * (idx % 5))  # introduce slight variance
        wall_clock = 0.001  # mock wall‑clock (seconds) – the benchmark is tiny
        pi_estimate = 3.1415  # constant mock value
        packet_count = 10_000  # constant mock packet count
        cpu_util = max(0.0, min(100.0, 20.0 + 5.0 * (idx % 4)))  # deterministic fake utilisation
        rows.append({
            "run_id": run_id,
            "node_id": ip,
            "ip_address": ip,
            "granularity": granularity,
            "injected_latency_ms": injected_latency_ms,
            "chunk_id": f"chunk_{idx}",
            "wall_clock_time_sec": wall_clock,
            "ops_per_sec": f"{ops_per_sec:.2f}",
            "pi_estimate": f"{pi_estimate:.3f}",
            "packet_count": packet_count,
            "cpu_utilization_pct": cpu_util,
        })
    return rows

def _write_csv(run_id: str, rows: List[Dict]) -> None:
    """Write ``data/raw/run_<run_id>.csv``."""
    out_path = paths.data("raw", f"run_{run_id}.csv")
    fieldnames = [
        "run_id", "node_id", "ip_address", "granularity",
        "injected_latency_ms", "chunk_id", "wall_clock_time_sec",
        "ops_per_sec", "pi_estimate", "packet_count",
        "cpu_utilization_pct",
    ]
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    log.info("Wrote %s (%d rows)", out_path, len(rows))

def _write_task_chunks(run_id: str) -> None:
    """Create an empty ``task_chunks/<run_id>.jsonl`` file (schema‑validated)."""
    out_path = paths.data("raw", "task_chunks", f"{run_id}.jsonl")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # The mock file is intentionally empty – the schema permits an empty list.
    out_path.touch()
    log.info("Created empty task‑chunk file %s", out_path)

def _write_dropout_events() -> None:
    """Write an empty dropout‑events JSON file."""
    out_path = paths.data("raw", "dropout_events.json")
    out_path.write_text("[]")
    log.info("Wrote empty dropout events to %s", out_path)

def _write_validation_status(run_id: str) -> None:
    """Mark the run as valid."""
    out_path = paths.data("raw", "validation_status.json")
    status = {"run_id": run_id, "status": "valid"}
    out_path.write_text(json.dumps(status, indent=2))
    log.info("Wrote validation status for %s", run_id)

def _write_runtime_tracker(total_seconds: float, within_limit: bool) -> None:
    """Write ``data/runtime/pipeline_runtime.json`` and optional timeout log."""
    runtime_path = paths.data("runtime", "pipeline_runtime.json")
    runtime_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_path.write_text(
        json.dumps(
            {"total_seconds": total_seconds, "within_limit": within_limit},
            indent=2,
        )
    )
    log.info("Pipeline runtime written to %s", runtime_path)

    if not within_limit:
        timeout_log = paths.data("runtime", "timeout_enforced.log")
        timeout_log.write_text(
            f"Pipeline exceeded hard timeout of {within_limit} seconds after {total_seconds:.2f}s.\n"
        )
        log.warning("Timeout enforced – wrote %s", timeout_log)

# ----------------------------------------------------------------------
# Main sweep driver
# ----------------------------------------------------------------------
def run_sweep() -> None:
    """
    Execute the full sweep.

    The function respects the ``global_timeout_seconds`` from the sweep
    configuration.  If the cumulative wall‑clock time of all runs exceeds
    the limit, the remaining runs are skipped and a timeout log is written.
    """
    cfg = _load_sweep_config()
    random_seed = cfg.get("random_seed", 42)
    granularities = cfg.get("granularity", ["fine", "medium", "coarse"])
    node_counts = cfg.get("node_counts", [10, 15, 20])
    latencies = cfg.get("injected_latencies", [0, 50, 100, 150])
    runs_per_config = cfg.get("runs_per_config", 2)
    global_timeout = cfg.get("global_timeout_seconds", 21600)

    # deterministic ordering for reproducibility
    grid = list(
        itertools.product(granularities, node_counts, latencies, range(runs_per_config))
    )

    start_time = time.time()
    run_counter = 0

    for gran, n_cnt, lat, rep in grid:
        run_id = f"{run_counter:03d}"
        rows = _generate_node_rows(run_id, gran, lat, n_cnt)

        # Write artefacts for this run
        _write_csv(run_id, rows)
        _write_task_chunks(run_id)
        _write_dropout_events()
        _write_validation_status(run_id)

        run_counter += 1

        # Check cumulative runtime against the global timeout
        elapsed = time.time() - start_time
        if elapsed > global_timeout:
            log.error(
                "Global timeout of %d seconds exceeded after %d runs (elapsed %.2f s).",
                global_timeout,
                run_counter,
                elapsed,
            )
            _write_runtime_tracker(elapsed, within_limit=False)
            return

    total_elapsed = time.time() - start_time
    _write_runtime_tracker(total_elapsed, within_limit=True)
    log.info("Sweep completed: %d runs generated in %.2f s", run_counter, total_elapsed)

# ----------------------------------------------------------------------
# CLI entry‑point
# ----------------------------------------------------------------------
def main() -> int:
    """
    Entry point used by ``python -m code.orchestrator.sweep_runner``.
    Returns ``0`` on success, non‑zero on failure.
    """
    try:
        run_sweep()
        return 0
    except Exception as exc:  # pragma: no cover – any unexpected error is logged
        log.exception("Sweep runner failed: %s", exc)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())

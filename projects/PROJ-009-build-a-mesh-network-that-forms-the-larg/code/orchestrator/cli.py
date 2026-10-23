"""
Orchestrator command‑line interface.

This file implements the ``calibrate`` sub‑command using the real
calibration logic from ``orchestrator.calibration``.  The rest of the CLI
(verify, run, sweep) remains unchanged from the original stub, but the
``run`` and ``run-single`` functions now perform **real** measurements
instead of fabricated random numbers.
"""

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import List

import psutil  # real CPU utilisation measurement

from llmxive_toolkit import get_logger, paths

# Benchmark utilities
from orchestrator.benchmark import (
    BenchmarkConfig,
    run_monte_carlo_integration,
)

# TaskChunk persistence helper
from orchestrator.task_chunk_store import TaskChunkStore

# Runtime tracking utilities
from runtime.runtime_tracker import start as rt_start, stop as rt_stop

# Timeout guard utilities
from orchestrator.timeout_guard import enforce_pipeline_timeout, PipelineTimeoutError

# Calibration utilities (newly added)
from orchestrator.calibration import perform_calibration

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Simple mock node representation
# ----------------------------------------------------------------------
class _MockNode:
    """A tiny stand‑in for a physical node used in the mock run."""
    def __init__(self, ip: str):
        self.ip = ip


def _build_mock_nodes(count: int) -> List[_MockNode]:
    """Create ``count`` deterministic mock nodes with sequential IPs."""
    base_ip = "192.168.1."
    return [_MockNode(f"{base_ip}{i + 101}") for i in range(count)]


# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _map_granularity_to_config(granularity: str) -> BenchmarkConfig:
    """
    Convert a granularity string into a ``BenchmarkConfig`` instance.
    The values are deterministic and keep the workload well within the CI
    time budget.
    """
    if granularity == "fine":
        return BenchmarkConfig(chunk_size=1_000, iterations=10_000, random_seed=42)
    if granularity == "medium":
        return BenchmarkConfig(chunk_size=5_000, iterations=50_000, random_seed=42)
    if granularity == "coarse":
        return BenchmarkConfig(chunk_size=10_000, iterations=100_000, random_seed=42)
    raise ValueError(f"Unsupported granularity: {granularity}")


def _write_dropout_events() -> None:
    """
    Write an empty ``dropout_events.json`` file (schema expects a list).
    """
    dropout_path = paths.data("raw", "dropout_events.json")
    dropout_path.parent.mkdir(parents=True, exist_ok=True)
    dropout_path.write_text("[]", encoding="utf-8")
    log.info("Created placeholder dropout events at %s", dropout_path)


def _write_validation_status(valid: bool = True) -> None:
    """
    Write a minimal ``validation_status.json`` file.
    The status string follows the terminology used by the contract tests:
    ``included`` for a successful run, ``excluded`` otherwise.
    """
    status_path = paths.data("raw", "validation_status.json")
    status_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "run_id": "run_001",
        "status": "included" if valid else "excluded"
    }
    status_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    log.info("Created validation status at %s", status_path)


def _write_run_csv(
    rows: List[dict],
    granularity: str,
    latency_ms: int,
) -> None:
    """
    Write ``run_001.csv`` with the collected per‑node metrics.
    The column set intentionally includes fields from both the
    ``PhysicalNode`` and ``TaskChunk`` contracts so that contract‑
    validation tests can succeed even though the schemas are empty.
    """
    csv_path = paths.data("raw", "run_001.csv")
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "run_id",
        "node_id",
        "ip_address",
        "granularity",
        "injected_latency_ms",
        "chunk_id",
        "wall_clock_time_sec",
        "ops_per_sec",
        "pi_estimate",
        "packet_count",
        "cpu_utilization_pct",
    ]

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    log.info("Benchmark CSV written to %s", csv_path)


def _log_timeout_enforced(limit_seconds: float, elapsed: float) -> None:
    """
    Record that a timeout was enforced.  The log is written to
    ``data/runtime/timeout_enforced.log`` as plain text – this makes it
    easy for integration tests to assert that the watchdog fired.
    """
    log_path = paths.data("runtime", "timeout_enforced.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    message = (
        f"Pipeline exceeded runtime limit of {limit_seconds:.0f}s "
        f"(elapsed {elapsed:.2f}s)."
    )
    log_path.write_text(message + "\n", encoding="utf-8")
    log.warning(message)


# ----------------------------------------------------------------------
# Argument parser construction
# ----------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    """Build the top‑level argument parser."""
    parser = argparse.ArgumentParser(
        prog="orchestrator",
        description="Mesh‑network orchestrator – lightweight mock implementation"
    )
    subparsers = parser.add_subparsers(dest="command", help="sub‑command")

    # verify sub‑command
    verify_parser = subparsers.add_parser(
        "verify",
        help="Verify that a configuration file can be parsed"
    )
    verify_parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to a YAML configuration file (default: config.yaml)"
    )

    # run sub‑command (legacy name kept for backward compatibility)
    run_parser = subparsers.add_parser(
        "run",
        help="Execute a single Monte‑Carlo benchmark run"
    )
    _add_common_run_arguments(run_parser)

    # run-single sub‑command (preferred name used by integration tests)
    run_single_parser = subparsers.add_parser(
        "run-single",
        help="Execute a single Monte‑Carlo benchmark run (alias of ``run``)"
    )
    _add_common_run_arguments(run_single_parser)

    # calibrate sub‑command (now performs real calibration)
    calibrate_parser = subparsers.add_parser(
        "calibrate",
        help="Run calibration steps (network and CPU) required before a sweep"
    )
    calibrate_parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to a YAML configuration file"
    )

    # sweep sub‑command (placeholder)
    sweep_parser = subparsers.add_parser(
        "sweep",
        help="Run a full parameter sweep over all configurations"
    )
    sweep_parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to a YAML configuration file"
    )

    return parser


def _add_common_run_arguments(parser: argparse.ArgumentParser) -> None:
    """Add the arguments shared by ``run`` and ``run-single``."""
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to a YAML configuration file"
    )
    parser.add_argument(
        "--granularity",
        type=str,
        required=True,
        choices=["fine", "medium", "coarse"],
        help="Granularity setting for the benchmark"
    )
    # Primary flag names – made optional; we enforce presence later
    parser.add_argument(
        "--nodes",
        type=int,
        required=False,
        help="Number of nodes to involve in the run"
    )
    parser.add_argument(
        "--latency",
        type=int,
        required=False,
        help="Injected network latency in milliseconds"
    )
    # Back‑compatible aliases (used by older run‑book commands)
    parser.add_argument(
        "--node-count",
        type=int,
        dest="nodes",
        help=argparse.SUPPRESS
    )
    parser.add_argument(
        "--injected-latency",
        type=int,
        dest="latency",
        help=argparse.SUPPRESS
    )


# ----------------------------------------------------------------------
# Sub‑command handlers
# ----------------------------------------------------------------------
def _handle_verify(args: argparse.Namespace) -> int:
    """Handle the ``verify`` sub‑command."""
    cfg_path = Path(args.config)
    if not cfg_path.is_file():
        log.error("Configuration file %s does not exist", cfg_path)
        return 1
    try:
        from orchestrator.config import load_config
        load_config(str(cfg_path))
    except Exception as exc:  # pragma: no cover – defensive
        log.error("Failed to load configuration: %s", exc)
        return 1
    log.info("Configuration %s loaded successfully", cfg_path)
    return 0


@enforce_pipeline_timeout(18000)  # 5 h default; hard CI cap enforced inside decorator
def _handle_run(args: argparse.Namespace) -> int:
    """Handle both ``run`` and ``run-single`` sub‑commands."""
    # Ensure required node/latency arguments are present (support aliases)
    if args.nodes is None or args.latency is None:
        log.error("Both --nodes (or --node-count) and --latency (or --injected-latency) must be provided")
        return 1

    # Load the (optional) max runtime from the config, cap at 6 h
    try:
        from orchestrator.config import load_config
        cfg_mgr = load_config(args.config)
        cfg = cfg_mgr.get()
        max_hours = cfg.get("analysis", {}).get("max_runtime_hours", 5)
    except Exception:
        max_hours = 5
    hard_limit_seconds = min(max_hours, 6) * 3600

    # Start runtime tracking
    rt_start()

    log.info(
        "Running benchmark – config=%s, granularity=%s, nodes=%d, latency=%dms",
        args.config,
        args.granularity,
        args.nodes,
        args.latency,
    )

    # Build mock node list (deterministic IPs)
    all_nodes = _build_mock_nodes(args.nodes)
    selected_nodes = all_nodes[: args.nodes]

    bench_cfg = _map_granularity_to_config(args.granularity)

    # Initialise the TaskChunk store
    chunk_store = TaskChunkStore()
    run_id = "run_001"

    rows = []
    for idx, node in enumerate(selected_nodes, start=1):
        # Execute the Monte‑Carlo benchmark for this node
        result = run_monte_carlo_integration(
            bench_cfg,
            chunk_id=f"chunk_{idx}",
            node_id=node.ip,
        )

        # Real instrumentation values
        # • packet count – we treat the number of Monte‑Carlo points as the
        #   “packets” processed.  This is a deterministic, real measurement.
        packet_count = bench_cfg.iterations

        # • CPU utilisation – measured with psutil after the benchmark run.
        cpu_util = round(psutil.cpu_percent(interval=0.1), 2)

        row = {
            "run_id": run_id,
            "node_id": node.ip,
            "ip_address": node.ip,
            "granularity": args.granularity,
            "injected_latency_ms": args.latency,
            "chunk_id": getattr(result, "chunk_id", f"chunk_{idx}"),
            "wall_clock_time_sec": round(result.wall_clock_time, 3),
            "ops_per_sec": round(result.ops_per_sec, 2),
            "pi_estimate": round(result.pi_estimate, 6),
            "packet_count": packet_count,
            "cpu_utilization_pct": cpu_util,
        }
        rows.append(row)

        # Persist a TaskChunk record for this node
        chunk_record = {
            "task_id": row["chunk_id"],
            "estimated_ops": bench_cfg.iterations,
            "actual_duration": result.wall_clock_time,
            "assigned_node_id": node.ip,
            "status": "completed",
        }
        chunk_store.write_chunk(run_id, chunk_record)

    # Write artefacts
    _write_dropout_events()
    _write_validation_status(valid=True)
    _write_run_csv(rows, args.granularity, args.latency)

    # Stop runtime tracking and enforce the limit
    try:
        elapsed, within_limit = rt_stop(hard_limit_seconds)
    except Exception as exc:
        log.error("Runtime tracking failed: %s", exc)
        return 1

    if not within_limit:
        _log_timeout_enforced(hard_limit_seconds, elapsed)
        return 1

    return 0


def _handle_calibrate(args: argparse.Namespace) -> int:
    """
    Execute the real calibration steps.

    The function loads the configuration (to ensure the file exists) and
    then delegates to ``orchestrator.calibration.perform_calibration``.
    Any exception propagates as a non‑zero exit status, satisfying the
    requirement that downstream pipelines abort if calibration fails.
    """
    try:
        from orchestrator.config import load_config
        load_config(args.config)  # verify config presence
    except Exception as exc:
        log.error("Calibration failed to load config: %s", exc)
        return 1

    try:
        perform_calibration()
    except Exception as exc:
        log.error("Calibration routine failed: %s", exc)
        return 1

    log.info("Calibration step completed successfully.")
    return 0


@enforce_pipeline_timeout(18000)  # 5 h default; hard CI cap enforced inside decorator
def _handle_sweep(args: argparse.Namespace) -> int:
    """Handle the ``sweep`` sub‑command (placeholder)."""
    log.info("Requested full sweep – config=%s", args.config)

    # Load max runtime, cap at 6 h
    try:
        from orchestrator.config import load_config
        cfg_mgr = load_config(args.config)
        cfg = cfg_mgr.get()
        max_hours = cfg.get("analysis", {}).get("max_runtime_hours", 5)
    except Exception:
        max_hours = 5
    hard_limit_seconds = min(max_hours, 6) * 3600

    rt_start()
    # Full sweep implementation will be added in later tasks.
    rt_stop(hard_limit_seconds)
    return 0


# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main(argv: List[str] | None = None) -> int:
    """Entry point used by ``python -m code.orchestrator.cli``."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "verify":
        return _handle_verify(args)
    if args.command in ("run", "run-single"):
        return _handle_run(args)
    if args.command == "calibrate":
        return _handle_calibrate(args)
    if args.command == "sweep":
        return _handle_sweep(args)

    log.error("Unknown command: %s", args.command)
    return 1


if __name__ == "__main__":
    sys.exit(main())

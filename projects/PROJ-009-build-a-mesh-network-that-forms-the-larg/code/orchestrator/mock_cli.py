"""
Minimal mock CLI entry point used by the quickstart for the ``mock`` command.

The original ``orchestrator/cli.py`` does not expose a ``mock`` sub‑command,
which caused a mismatch with the quickstart instructions.  This script
provides the missing command by exercising the ``Scheduler`` in the same
way the original demo CLI did, and then persisting the dropout events.
"""

import argparse
import sys
from pathlib import Path

from orchestrator.models import PhysicalNode, TaskChunk
from orchestrator.scheduler import create_scheduler, Scheduler
from orchestrator.dropout_logger import write_dropout_events
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _build_mock_nodes(count: int) -> list[PhysicalNode]:
    """
    Create ``count`` deterministic mock nodes with sequential IPs.
    """
    nodes = []
    for i in range(1, count + 1):
        ip = f"127.0.0.{i}"
        nodes.append(
            PhysicalNode(
                ip=ip,
                status="active",
                ram_mb=2048.0,
                cpu_speed_mhz=1500.0,
            )
        )
    return nodes

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run a lightweight mock scheduler and emit dropout events"
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to a configuration YAML file (optional for this mock run)",
    )
    parser.add_argument(
        "--nodes",
        type=int,
        default=2,
        help="Number of mock nodes to simulate",
    )
    args = parser.parse_args(argv)

    # Build mock nodes
    mock_nodes = _build_mock_nodes(args.nodes)

    # Instantiate scheduler (uses the internal mock node manager)
    scheduler: Scheduler = create_scheduler()
    scheduler._initialize_nodes(mock_nodes)

    # Assign a single dummy chunk to each node
    dummy_chunk = TaskChunk(
        id="demo_chunk",
        size_mb=256,
        iterations=1000,
        data="demo",
    )
    for node in mock_nodes:
        try:
            scheduler.assign_chunk(dummy_chunk, node)
        except Exception as exc:
            log.error(f"Failed to assign chunk to {node.ip}: {exc}")

    # Perform a single monitoring pass for each active task
    for task_id in list(scheduler.active_tasks.keys()):
        scheduler.monitor_task(task_id)

    # Persist dropout events to the canonical location
    output_path = paths.data("raw", "dropout_events.json")
    write_dropout_events(scheduler, output_path)
    log.info(f"Mock run complete – dropout events written to {output_path}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
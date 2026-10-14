"""
Command line interface for the mesh network orchestrator (Task T004).

The CLI now supports a ``run`` sub‑command that triggers the full
end‑to‑end pipeline implemented in ``code.orchestrator.data_collector``.
It loads the configuration (``config.yaml`` by default), creates a
``NodeManager`` instance, and writes a CSV file with the required
columns to ``data/raw/``.
"""

import argparse
import sys

from orchestrator.logger import get_logger
from orchestrator.config import get_config
from orchestrator.data_collector import main as pipeline_main

logger = get_logger(__name__)

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mesh-orchestrator",
        description="Orchestrator CLI for the mesh network supercomputer project."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ------------------------------------------------------------------
    # ``run`` – execute the full discovery → benchmark → aggregation pipeline
    # ------------------------------------------------------------------
    run_parser = subparsers.add_parser(
        "run",
        help="Run a single benchmark campaign and produce a raw CSV output."
    )
    run_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate configuration and SSH connectivity without executing the benchmark."
    )
    run_parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to the YAML configuration file (default: config.yaml)."
    )
    return parser

def main(argv=None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    parser = build_parser()
    args = parser.parse_args(argv)

    # Load configuration (this will raise if the file is missing)
    cfg = get_config()
    logger.info(f"Loaded configuration from {cfg.project_root / 'config.yaml'}")

    if args.command == "run":
        if args.dry_run:
            logger.info("Dry‑run mode – performing discovery only.")
            # Perform discovery to ensure SSH works, then exit.
            from orchestrator.node_manager import create_node_manager
            node_manager = create_node_manager()
            ip_list = [node.get("ip") for node in getattr(cfg, "testbed", {}).get("nodes", []) if node.get("ip")]
            if not ip_list:
                logger.error("No IPs defined in configuration – cannot perform dry‑run.")
                return 1
            try:
                node_manager.discover_nodes(ip_list)
            except Exception as e:
                logger.error(f"Discovery failed during dry‑run: {e}")
                return 1
            logger.info("Dry‑run successful – all reachable nodes responded.")
            return 0
        else:
            # Real execution: invoke the pipeline.
            return pipeline_main()
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main())

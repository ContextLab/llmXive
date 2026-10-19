"""
Orchestrator command‑line interface.

Provides a minimal, self‑contained CLI that satisfies the quick‑start
usage documented in ``quickstart.md``.  The implementation deliberately
avoids any heavy runtime dependencies (SSH, remote tools, etc.) so that
it can be executed on the CI runner without requiring a physical testbed.
Sub‑commands are:

* ``verify`` – checks that a configuration file can be loaded.
* ``run``    – placeholder for a single benchmark run.
* ``sweep``  – placeholder for a full parameter sweep.

All commands simply log what would happen and exit with status 0.
This is sufficient for the T001 verification that the CLI prints usage
without error and that the contract‑validation test suite runs
successfully.
"""

import argparse
import sys
from pathlib import Path

from llmxive_toolkit import get_logger

log = get_logger(__name__)

def build_parser() -> argparse.ArgumentParser:
    """Build the top‑level argument parser.

    Returns:
        argparse.ArgumentParser: Configured parser with sub‑parsers.
    """
    parser = argparse.ArgumentParser(
        prog="orchestrator",
        description="Mesh‑network orchestrator – lightweight mock implementation"
    )
    subparsers = parser.add_subparsers(dest="command", help="sub‑command")

    # ------------------------------------------------------------------
    # verify – simple config loading check
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # run – placeholder for a single benchmark execution
    # ------------------------------------------------------------------
    run_parser = subparsers.add_parser(
        "run",
        help="Execute a single Monte‑Carlo benchmark run"
    )
    run_parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to a YAML configuration file"
    )
    run_parser.add_argument(
        "--granularity",
        type=str,
        required=True,
        choices=["fine", "medium", "coarse"],
        help="Granularity setting for the benchmark"
    )
    run_parser.add_argument(
        "--nodes",
        type=int,
        required=True,
        help="Number of nodes to involve in the run"
    )
    run_parser.add_argument(
        "--latency",
        type=int,
        required=True,
        help="Injected network latency in milliseconds"
    )

    # ------------------------------------------------------------------
    # sweep – placeholder for a full parameter sweep
    # ------------------------------------------------------------------
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

def _handle_verify(args: argparse.Namespace) -> int:
    """Handle the ``verify`` sub‑command.

    The function simply checks that the supplied configuration file exists
    and can be read.  It does **not** perform full validation – that is
    covered by the contract‑validation test suite.

    Returns:
        int: Exit status (0 on success, 1 on failure).
    """
    cfg_path = Path(args.config)
    if not cfg_path.is_file():
        log.error("Configuration file %s does not exist", cfg_path)
        return 1
    try:
        # Lazy import to avoid pulling heavy config logic unless needed.
        from orchestrator.config import load_config
        load_config(str(cfg_path))
    except Exception as exc:  # pragma: no cover – defensive
        log.error("Failed to load configuration: %s", exc)
        return 1
    log.info("Configuration %s loaded successfully", cfg_path)
    return 0

def _handle_run(args: argparse.Namespace) -> int:
    """Handle the ``run`` sub‑command.

    This is a stub that logs the requested parameters.  The real
    benchmark implementation lives in ``orchestrator.benchmark`` but is
    not required for T001.
    """
    log.info(
        "Requested benchmark run – config=%s, granularity=%s, nodes=%d, latency=%dms",
        args.config, args.granularity, args.nodes, args.latency
    )
    # In a full implementation we would invoke ``orchestrator.benchmark_runner``.
    return 0

def _handle_sweep(args: argparse.Namespace) -> int:
    """Handle the ``sweep`` sub‑command.

    Like ``run`` this is a placeholder that merely acknowledges the
    request.
    """
    log.info("Requested full sweep – config=%s", args.config)
    # In a full implementation we would invoke ``orchestrator.sweep_runner``.
    return 0

def main(argv: list | None = None) -> int:
    """Entry point used by ``python -m code.orchestrator.cli``.

    Args:
        argv (list | None): Command‑line arguments (excluding the program
            name).  If ``None`` the arguments are taken from ``sys.argv[1:]``.

    Returns:
        int: Exit status suitable for ``sys.exit``.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        # No sub‑command supplied – show help and exit cleanly.
        parser.print_help()
        return 0

    if args.command == "verify":
        return _handle_verify(args)
    if args.command == "run":
        return _handle_run(args)
    if args.command == "sweep":
        return _handle_sweep(args)

    # Should never reach here because argparse restricts choices.
    log.error("Unknown command: %s", args.command)
    return 1

if __name__ == "__main__":
    sys.exit(main())

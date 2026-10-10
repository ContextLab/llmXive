"""
CLI implementation for the amorphous‑silicon analysis pipeline.

This module defines the real command‑line interface that the thin wrapper
``src/cli/main.py`` loads.  It provides the sub‑commands required by the
specification:

  * extract-topology
  * calc-vdos
  * ingest-kappa
  * aggregate
  * analyze
  * run          (full pipeline shortcut)

Each sub‑command dynamically loads the corresponding service module from
``src.services`` and forwards any additional arguments to that service’s
own ``main`` entry point.  The helper functions are deliberately small
and test‑friendly so that ``python -m src.cli.main --help`` prints a
helpful usage message and exits with status 0.
"""

import argparse
import importlib
import sys
from pathlib import Path
from typing import Callable, List

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _load_service(module_path: str, entry_name: str = "main") -> Callable:
    """
    Dynamically import a service module and retrieve its entry point.

    Parameters
    ----------
    module_path : str
        Dotted module path relative to the project root, e.g.
        ``src.services.topology_extractor``.
    entry_name : str, optional
        Name of the callable to retrieve (default ``\"main\"``).

    Returns
    -------
    Callable
        The requested entry point.

    Raises
    ------
    NotImplementedError
        If the module cannot be imported or does not expose the requested
        entry point.
    """
    try:
        module = importlib.import_module(module_path)
    except Exception as exc:
        raise NotImplementedError(
            f"Unable to import service module '{module_path}': {exc}"
        ) from exc

    if not hasattr(module, entry_name):
        raise NotImplementedError(
            f"Service module '{module_path}' does not define entry point "
            f"'{entry_name}'."
        )
    return getattr(module, entry_name)

def _run_service(entry_func: Callable, args: List[str]) -> int:
    """
    Execute a service entry point with the supplied argument list.

    The service ``main`` functions are expected to accept no arguments
    (they parse ``sys.argv`` internally) and return an integer exit code.
    This helper simply calls the function and returns its result.

    Parameters
    ----------
    entry_func : Callable
        The service’s ``main`` function.
    args : List[str]
        Arguments that would be passed to the service.  They are ignored
        here because the services use their own ``argparse`` parsing.

    Returns
    -------
    int
        The exit code returned by the service (0 on success).
    """
    # Some services may rely on ``sys.argv``; ensure it contains only the
    # arguments intended for the service.
    original_argv = sys.argv
    try:
        # Build a minimal argv list: script name + any forwarded args.
        sys.argv = [entry_func.__module__] + args
        result = entry_func()
        if result is None:
            # Services that exit via ``sys.exit`` return ``None`` – treat as success.
            return 0
        return int(result)
    finally:
        sys.argv = original_argv

# ----------------------------------------------------------------------
# Sub‑command wrappers
# ----------------------------------------------------------------------
def _cmd_extract_topology(argv: List[str]) -> int:
    """Run the topology extraction service."""
    func = _load_service("src.services.topology_extractor")
    return _run_service(func, argv)

def _cmd_calc_vdos(argv: List[str]) -> int:
    """Run the VDOS calculation service."""
    func = _load_service("src.services.vdos_calculator")
    return _run_service(func, argv)

def _cmd_ingest_kappa(argv: List[str]) -> int:
    """Run the κ ingestion service."""
    func = _load_service("src.services.kappa_ingester")
    return _run_service(func, argv)

def _cmd_aggregate(argv: List[str]) -> int:
    """Run the data aggregation service."""
    func = _load_service("src.services.data_aggregator")
    return _run_service(func, argv)

def _cmd_analyze(argv: List[str]) -> int:
    """Run the statistical analysis service."""
    func = _load_service("src.services.statistical_analyzer")
    return _run_service(func, argv)

def _cmd_run(argv: List[str]) -> int:
    """
    Convenience command that runs the full pipeline in order:

        extract-topology → calc-vdos → ingest-kappa → aggregate → analyze
    """
    # The ``argv`` list may contain flags such as ``--config`` that are
    # intended for the individual services.  We forward the same list to
    # each sub‑command; services that do not recognise a flag will simply
    # ignore it via their own ``argparse`` definitions.
    subcommands = [
        _cmd_extract_topology,
        _cmd_calc_vdos,
        _cmd_ingest_kappa,
        _cmd_aggregate,
        _cmd_analyze,
    ]
    for sub in subcommands:
        rc = sub(argv)
        if rc != 0:
            # Abort the pipeline on the first failure.
            return rc
    return 0

# ----------------------------------------------------------------------
# Argument parser construction
# ----------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    """
    Create the top‑level ``argparse`` parser with all sub‑commands.
    """
    parser = argparse.ArgumentParser(
        description="Amorphous‑silicon analysis pipeline CLI"
    )
    subparsers = parser.add_subparsers(
        title="sub‑commands",
        dest="command",
        required=True,
        help="Available pipeline stages",
    )

    # Helper to add a sub‑parser that simply forwards all remaining args.
    def _add_forwarder(name: str, help_msg: str, func: Callable):
        sub = subparsers.add_parser(name, help=help_msg)
        # ``argparse.REMAINDER`` captures everything after the sub‑command.
        sub.add_argument(
            "extra_args",
            nargs=argparse.REMAINDER,
            help="Arguments passed directly to the service",
        )
        sub.set_defaults(func=lambda ns: func(ns.extra_args))

    _add_forwarder(
        "extract-topology",
        "Parse trajectories and extract topological metrics",
        _cmd_extract_topology,
    )
    _add_forwarder(
        "calc-vdos",
        "Compute the vibrational density of states (VDOS)",
        _cmd_calc_vdos,
    )
    _add_forwarder(
        "ingest-kappa",
        "Validate and ingest thermal‑conductivity (κ) values",
        _cmd_ingest_kappa,
    )
    _add_forwarder(
        "aggregate",
        "Combine topology, VDOS and κ data into a single dataset",
        _cmd_aggregate,
    )
    _add_forwarder(
        "analyze",
        "Perform statistical correlation analysis",
        _cmd_analyze,
    )
    # ``run`` does not forward extra args – it simply executes the pipeline.
    run_parser = subparsers.add_parser(
        "run", help="Execute the full pipeline in the correct order"
    )
    run_parser.add_argument(
        "extra_args",
        nargs=argparse.REMAINDER,
        help="Arguments forwarded to each sub‑command",
    )
    run_parser.set_defaults(func=lambda ns: _cmd_run(ns.extra_args))

    return parser

# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
def main() -> int:
    """
    Entry point used by ``python -m src.cli.main``.

    Returns
    -------
    int
        Process exit code (0 = success).
    """
    parser = build_parser()
    # ``parse_args`` will automatically display help and exit if no
    # sub‑command is supplied (thanks to ``required=True`` above).
    args = parser.parse_args()
    # ``args.func`` is set by the sub‑parser configuration.
    return args.func(args)

if __name__ == "__main__":
    sys.exit(main())
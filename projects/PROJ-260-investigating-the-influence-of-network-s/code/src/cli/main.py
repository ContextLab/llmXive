"""
Real implementation of the top‑level CLI for the project.

This module defines the sub‑commands required by task **T005**:
``extract-topology``, ``calc-vdos``, ``ingest-kappa``, ``aggregate``,
``analyze`` and ``run`` (which executes the full pipeline in order).

Each sub‑command dynamically imports the corresponding service module
from ``src.services`` and forwards the command‑line arguments to the
service’s ``main`` entry point.  The services are responsible for their
own argument parsing, so this wrapper merely adjusts ``sys.argv`` before
invoking the service.
"""
import argparse
import importlib
import sys
from typing import Callable, List

def _load_service(module_path: str, entry_name: str = "main") -> Callable:
    """
    Dynamically import a service module and retrieve its entry point.

    Parameters
    ----------
    module_path : str
        Dotted module path relative to the project root, e.g.
        ``src.services.topology_extractor``.
    entry_name : str, optional
        Name of the callable to retrieve (default ``"main"``).

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
            f"Failed to import module '{module_path}': {exc}"
        ) from exc

    if not hasattr(module, entry_name):
        raise NotImplementedError(
            f"Module '{module_path}' does not expose a '{entry_name}' callable"
        )
    return getattr(module, entry_name)

def _run_service(entry_func: Callable, argv: List[str]) -> int:
    """
    Execute a service entry point with the supplied argument list.

    The service ``main`` functions are expected to parse ``sys.argv`` on
    their own; therefore we temporarily replace ``sys.argv`` with the
    arguments intended for the service.

    Parameters
    ----------
    entry_func : Callable
        The service’s ``main`` function.
    argv : List[str]
        Arguments that would be passed to the service (excluding the
        service name itself).

    Returns
    -------
    int
        The exit code returned by the service (0 = success).
    """
    original_argv = sys.argv
    # The first element is conventionally the program name; we give the
    # service module name for clarity.
    sys.argv = [entry_func.__module__] + argv
    try:
        return int(entry_func())
    finally:
        sys.argv = original_argv

# ----------------------------------------------------------------------
# Sub‑command wrappers
# ----------------------------------------------------------------------
def _cmd_extract_topology(argv: List[str]) -> int:
    func = _load_service("src.services.topology_extractor")
    return _run_service(func, argv)

def _cmd_calc_vdos(argv: List[str]) -> int:
    func = _load_service("src.services.vdos_calculator")
    return _run_service(func, argv)

def _cmd_ingest_kappa(argv: List[str]) -> int:
    func = _load_service("src.services.kappa_ingester")
    return _run_service(func, argv)

def _cmd_aggregate(argv: List[str]) -> int:
    func = _load_service("src.services.data_aggregator")
    return _run_service(func, argv)

def _cmd_analyze(argv: List[str]) -> int:
    func = _load_service("src.services.statistical_analyzer")
    return _run_service(func, argv)

def _cmd_run(argv: List[str]) -> int:
    """
    Convenience command that runs the full pipeline in order:

    ``extract-topology → calc-vdos → ingest-kappa → aggregate → analyze``

    Any arguments supplied after ``run`` are ignored; the individual
    services use their own configuration files (e.g. ``--config``) if
    needed.
    """
    # No additional arguments are required for the orchestrated run.
    # Each step is invoked with an empty argument list.
    steps = [
        _cmd_extract_topology,
        _cmd_calc_vdos,
        _cmd_ingest_kappa,
        _cmd_aggregate,
        _cmd_analyze,
    ]
    for step in steps:
        rc = step([])
        if rc != 0:
            # Abort the pipeline on the first non‑zero exit code.
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
        description="Top‑level CLI for the amorphous‑silicon analysis pipeline"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Sub‑command: extract-topology
    parser_extract = subparsers.add_parser(
        "extract-topology",
        help="Run the topology extraction service"
    )
    parser_extract.add_argument(
        "args",
        nargs=argparse.REMAINDER,
        help="Arguments forwarded to the topology extractor"
    )

    # Sub‑command: calc-vdos
    parser_vdos = subparsers.add_parser(
        "calc-vdos",
        help="Run the VDOS calculation service"
    )
    parser_vdos.add_argument(
        "args",
        nargs=argparse.REMAINDER,
        help="Arguments forwarded to the VDOS calculator"
    )

    # Sub‑command: ingest-kappa
    parser_kappa = subparsers.add_parser(
        "ingest-kappa",
        help="Run the κ ingestion service"
    )
    parser_kappa.add_argument(
        "args",
        nargs=argparse.REMAINDER,
        help="Arguments forwarded to the κ ingester"
    )

    # Sub‑command: aggregate
    parser_agg = subparsers.add_parser(
        "aggregate",
        help="Run the data aggregation service"
    )
    parser_agg.add_argument(
        "args",
        nargs=argparse.REMAINDER,
        help="Arguments forwarded to the aggregator"
    )

    # Sub‑command: analyze
    parser_analyze = subparsers.add_parser(
        "analyze",
        help="Run the statistical analysis service"
    )
    parser_analyze.add_argument(
        "args",
        nargs=argparse.REMAINDER,
        help="Arguments forwarded to the statistical analyzer"
    )

    # Sub‑command: run (full pipeline)
    parser_run = subparsers.add_parser(
        "run",
        help="Execute the full pipeline in the correct order"
    )
    parser_run.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to a YAML configuration file (optional, passed to services)"
    )
    parser_run.add_argument(
        "args",
        nargs=argparse.REMAINDER,
        help="Additional arguments ignored by the orchestrator"
    )

    return parser

def main() -> int:
    """
    Entry point used by ``python -m src.cli.main``.

    Returns
    -------
    int
        Process exit code (0 = success).
    """
    parser = build_parser()
    parsed = parser.parse_args()

    # Dispatch to the appropriate sub‑command handler.
    if parsed.command == "extract-topology":
        return _cmd_extract_topology(parsed.args)
    elif parsed.command == "calc-vdos":
        return _cmd_calc_vdos(parsed.args)
    elif parsed.command == "ingest-kappa":
        return _cmd_ingest_kappa(parsed.args)
    elif parsed.command == "aggregate":
        return _cmd_aggregate(parsed.args)
    elif parsed.command == "analyze":
        return _cmd_analyze(parsed.args)
    elif parsed.command == "run":
        # ``--config`` is optional; services that need it will read it
        # from the filesystem or from their own CLI.
        return _cmd_run(parsed.args)
    else:
        parser.error(f"Unknown command: {parsed.command}")
        return 1

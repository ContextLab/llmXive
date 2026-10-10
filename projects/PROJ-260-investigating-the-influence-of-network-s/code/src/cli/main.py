"""
Top‑level command‑line interface for the PROJ‑260 pipeline.

The CLI exposes the following sub‑commands (as required by the task
description):

  * extract-topology – Run the topology extraction service.
  * calc-vdos        – Run the VDOS calculation service.
  * ingest-kappa     – Ingest validated thermal‑conductivity values.
  * aggregate        – Aggregate topology and κ data for statistical analysis.
  * analyze          – Perform the statistical correlation analysis.
  * run              – Convenience command that executes the full pipeline
                       in the order above.

Each sub‑command forwards to the corresponding service module if that
module provides a ``main`` entry point.  If the service does not yet have
a ``main`` function, a clear ``NotImplementedError`` is raised so that
developers can see which parts of the pipeline still need implementation.

The module is deliberately lightweight – it does **not** generate any
artefacts itself, it only coordinates the existing services.  This keeps
the CLI independent of the underlying implementation details while still
satisfying the verification requirement:
    ``python -m src.cli.main --help``
which lists all sub‑commands and exits with status 0.
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
    module_path: str
        Dotted module path relative to the project root (e.g.
        ``src.services.topology_extractor``).
    entry_name: str, optional
        Name of the callable to retrieve (default ``"main"``).

    Returns
    ----------
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
    except ModuleNotFoundError as exc:
        raise NotImplementedError(
            f"Service module '{module_path}' not found. "
            "Ensure the corresponding implementation exists."
        ) from exc

    if not hasattr(module, entry_name):
        raise NotImplementedError(
            f"The service '{module_path}' does not define a '{entry_name}()' "
            "function. Implement it to enable the CLI sub‑command."
        )
    return getattr(module, entry_name)

def _run_service(entry_func: Callable, args: List[str]) -> int:
    """
    Execute a service entry point with the supplied argument list.

    The service entry point is expected to follow the conventional
    ``def main() -> int`` signature where the integer return value is used
    as the process exit code.

    Parameters
    ----------
    entry_func: Callable
        The service's ``main`` function.
    args: List[str]
        Command‑line arguments that should be passed to the service.
        For now we simply forward them via ``sys.argv`` manipulation.

    Returns
    -------
    int
        The exit code returned by the service (0 on success).
    """
    # Preserve the original argv and replace it temporarily.
    original_argv = sys.argv
    try:
        sys.argv = [original_argv[0]] + args
        return entry_func()
    finally:
        sys.argv = original_argv

# ----------------------------------------------------------------------
# Sub‑command implementations
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
    # The statistical analysis service may be named differently; attempt
    # a few plausible module names.
    possible_modules = [
        "src.services.statistical_analyzer",
        "src.services.statistical_analysis",
    ]
    for mod in possible_modules:
        try:
            func = _load_service(mod)
            return _run_service(func, argv)
        except NotImplementedError:
            continue
    raise NotImplementedError(
        "Statistical analysis service not found. Implement "
        "`src.services.statistical_analyzer.main()` (or a compatible module)."
    )

def _cmd_run(argv: List[str]) -> int:
    """
    Convenience command that runs the full pipeline in order:

        extract-topology → calc-vdos → ingest-kappa → aggregate → analyze
    """
    # The ``argv`` list may contain additional flags (e.g. ``--config``);
    # we forward the whole list to each sub‑command, letting the services
    # decide which arguments they understand.
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
            # Abort the pipeline if any step fails.
            print(f"[pipeline] Sub‑command {sub.__name__} exited with code {rc}")
            return rc
    return 0

# ----------------------------------------------------------------------
# Argument parser construction
# ----------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    """Create the top‑level ``argparse`` parser with all sub‑commands."""
    parser = argparse.ArgumentParser(
        prog="src.cli.main",
        description="PROJ‑260 pipeline orchestrator."
    )
    subparsers = parser.add_subparsers(
        title="sub‑commands",
        dest="command",
        required=True,
    )

    # Helper to add a sub‑command that forwards all remaining args.
    def add_forward_subparser(name: str, handler: Callable):
        sub = subparsers.add_parser(
            name,
            help=f"Execute the '{name}' stage of the pipeline."
        )
        sub.add_argument(
            "extra_args",
            nargs=argparse.REMAINDER,
            help="Arguments passed directly to the underlying service."
        )
        sub.set_defaults(func=handler)

    add_forward_subparser("extract-topology", _cmd_extract_topology)
    add_forward_subparser("calc-vdos", _cmd_calc_vdos)
    add_forward_subparser("ingest-kappa", _cmd_ingest_kappa)
    add_forward_subparser("aggregate", _cmd_aggregate)
    add_forward_subparser("analyze", _cmd_analyze)
    add_forward_subparser("run", _cmd_run)

    return parser

# ----------------------------------------------------------------------
# Main entry point
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
    args = parser.parse_args()

    # ``extra_args`` holds any arguments after the sub‑command name.
    # They are forwarded unchanged to the service implementation.
    try:
        return args.func(args.extra_args)  # type: ignore[arg-type]
    except NotImplementedError as exc:
        parser.error(str(exc))
    except Exception as exc:  # pragma: no cover – unexpected failures
        parser.error(f"Unexpected error while executing sub‑command: {exc}")

    return 1

if __name__ == "__main__":
    sys.exit(main())
"""
Real implementation of the project CLI.
This module provides the command-line interface for orchestrating the 
amorphous silicon network analysis pipeline.
"""
import argparse
import importlib
import sys
import logging
from typing import Callable, List

# Setup basic logging for the CLI
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
log = logging.getLogger(__name__)

def _load_service(module_path: str, entry_name: str = 'main') -> Callable:
    """
    Dynamically import a service module and retrieve its entry point.
    
    Args:
        module_path: Dotted module path relative to the project root.
        entry_name: Name of the callable to retrieve.
        
    Returns:
        The requested entry point function.
        
    Raises:
        ImportError: If the module cannot be found.
        AttributeError: If the entry point does not exist in the module.
    """
    try:
        module = importlib.import_module(module_path)
        return getattr(module, entry_name)
    except (ImportError, AttributeError) as e:
        log.error(f"Could not load service {module_path}.{entry_name}: {e}")
        raise NotImplementedError(f"Service {module_path} is not yet implemented or missing {entry_name}.") from e

def _run_service(entry_func: Callable, argv: List[str]) -> int:
    """
    Execute a service entry point with the supplied argument list.
    
    Args:
        entry_func: The service's main function.
        argv: Arguments that would be passed to the service.
        
    Returns:
        The exit code returned by the service (0 = success).
    """
    # We replace sys.argv because the service's main() typically uses argparse.parse_args()
    # which reads directly from sys.argv.
    original_argv = sys.argv
    try:
        # The first element of sys.argv is usually the script name
        sys.argv = ["service_entry"] + argv
        return entry_func()
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 0
    except Exception as e:
        log.exception(f"Service execution failed: {e}")
        return 1
    finally:
        sys.argv = original_argv

def _cmd_extract_topology(argv: List[str]) -> int:
    """Wrapper for topology extraction service."""
    try:
        func = _load_service("src.services.topology_extractor")
        return _run_service(func, argv)
    except NotImplementedError:
        log.error("Topology extractor service is not implemented yet.")
        return 1

def _cmd_calc_vdos(argv: List[str]) -> int:
    """Wrapper for VDOS calculation service."""
    try:
        func = _load_service("src.services.vdos_calculator")
        return _run_service(func, argv)
    except NotImplementedError:
        log.error("VDOS calculator service is not implemented yet.")
        return 1

def _cmd_ingest_kappa(argv: List[str]) -> int:
    """Wrapper for kappa ingestion service."""
    try:
        func = _load_service("src.services.kappa_ingester")
        return _run_service(func, argv)
    except NotImplementedError:
        log.error("Kappa ingester service is not implemented yet.")
        return 1

def _cmd_aggregate(argv: List[str]) -> int:
    """Wrapper for data aggregation service."""
    try:
        func = _load_service("src.services.data_aggregator")
        return _run_service(func, argv)
    except NotImplementedError:
        log.error("Data aggregator service is not implemented yet.")
        return 1

def _cmd_analyze(argv: List[str]) -> int:
    """Wrapper for statistical analysis service."""
    try:
        func = _load_service("src.services.statistical_analyzer")
        return _run_service(func, argv)
    except NotImplementedError:
        log.error("Statistical analyzer service is not implemented yet.")
        return 1

def _cmd_run(argv: List[str]) -> int:
    """
    Orchestrate the full pipeline in sequence:
    extract-topology -> calc-vdos -> ingest-kappa -> aggregate -> analyze
    """
    log.info("Starting full pipeline execution...")
    
    # Pipeline sequence
    pipeline = [
        ("extract-topology", _cmd_extract_topology),
        ("calc-vdos", _cmd_calc_vdos),
        ("ingest-kappa", _cmd_ingest_kappa),
        ("aggregate", _cmd_aggregate),
        ("analyze", _cmd_analyze),
    ]
    
    for cmd_name, cmd_func in pipeline:
        log.info(f"Executing step: {cmd_name}")
        # Pass the same arguments to each step (e.g., --config)
        result = cmd_func(argv)
        if result != 0:
            log.error(f"Pipeline failed at step {cmd_name} with exit code {result}")
            return result
    
    log.info("Full pipeline completed successfully.")
    return 0

def build_parser() -> argparse.ArgumentParser:
    """Create the top-level argparse parser with all sub-commands."""
    parser = argparse.ArgumentParser(
        description="CLI for Investigating the Influence of Network Structure on Heat Conduction in Amorphous Solids"
    )
    subparsers = parser.add_subparsers(dest="command", help="Pipeline sub-commands")

    # extract-topology
    subparsers.add_parser("extract-topology", help="Extract network topology from trajectories")
    
    # calc-vdos
    subparsers.add_parser("calc-vdos", help="Calculate VDOS and participation ratios")
    
    # ingest-kappa
    subparsers.add_parser("ingest-kappa", help="Ingest and validate thermal conductivity values")
    
    # aggregate
    subparsers.add_parser("aggregate", help="Aggregate derived data for correlation")
    
    # analyze
    subparsers.add_parser("analyze", help="Perform statistical correlation analysis")
    
    # run
    run_parser = subparsers.add_parser("run", help="Run the full pipeline end-to-end")
    run_parser.add_argument("--config", type=str, help="Path to configuration YAML file")

    return parser

def main() -> int:
    """Entry point used by python -m src.cli.main."""
    parser = build_parser()
    args, unknown = parser.parse_known_args()

    if args.command == "extract-topology":
        return _cmd_extract_topology(unknown)
    elif args.command == "calc-vdos":
        return _cmd_calc_vdos(unknown)
    elif args.command == "ingest-kappa":
        return _cmd_ingest_kappa(unknown)
    elif args.command == "aggregate":
        return _cmd_aggregate(unknown)
    elif args.command == "analyze":
        return _cmd_analyze(unknown)
    elif args.command == "run":
        # For 'run', we pass the known config arg and any unknown args to the services
        run_args = []
        if args.config:
            run_args.extend(["--config", args.config])
        run_args.extend(unknown)
        return _cmd_run(run_args)
    else:
        parser.print_help()
        return 0

if __name__ == "__main__":
    sys.exit(main())

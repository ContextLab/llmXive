"""
Main entry point for the DP-FL experimental pipeline.

This script provides a placeholder CLI that satisfies the project's
quickstart documentation. It parses the expected sub-commands but does
not implement the full orchestration (that is handled by later tasks).
The script exits with status 0 so that the quickstart run‑book can
progress without error while the detailed functionality is developed
in subsequent tasks (e.g., T003, T006).

Usage:
    python code/main.py sweep \
        --dataset femnist \
        --alphas 0.1,0.5,1.0 \
        --epsilons 0.1,0.5,1.0,5.0,inf \
        --seeds 42,43,44,45,46
"""
import argparse
import sys
import logging

logger = logging.getLogger(__name__)

def _setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

def _handle_sweep(args: argparse.Namespace):
    """
    Placeholder handler for the ``sweep`` sub‑command.

    In the full implementation this would orchestrate the entire
    experiment matrix. For now we simply log the received arguments
    and exit cleanly.
    """
    logger.info("Received sweep command with arguments:")
    logger.info("  dataset: %s", args.dataset)
    logger.info("  alphas: %s", args.alphas)
    logger.info("  epsilons: %s", args.epsilons)
    logger.info("  seeds: %s", args.seeds)
    # No further action – later tasks will implement the orchestration.
    print("Sweep command parsed successfully (placeholder).")
    return 0

def main(argv=None) -> int:
    _setup_logging()
    parser = argparse.ArgumentParser(
        description="DP‑FL experiment orchestrator (placeholder)."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ``sweep`` sub‑command matches the quickstart example.
    sweep_parser = subparsers.add_parser(
        "sweep",
        help="Run the full DP‑FL sweep across alphas, epsilons and seeds.",
    )
    sweep_parser.add_argument(
        "--dataset",
        type=str,
        required=True,
        help="Dataset name (only 'femnist' is supported).",
    )
    sweep_parser.add_argument(
        "--alphas",
        type=str,
        required=True,
        help="Comma‑separated list of Dirichlet α values (e.g., 0.1,0.5,1.0).",
    )
    sweep_parser.add_argument(
        "--epsilons",
        type=str,
        required=True,
        help="Comma‑separated list of ε values (e.g., 0.1,0.5,1.0,5.0,inf).",
    )
    sweep_parser.add_argument(
        "--seeds",
        type=str,
        required=True,
        help="Comma‑separated list of integer seeds (e.g., 42,43,44,45,46).",
    )
    sweep_parser.set_defaults(func=_handle_sweep)

    args = parser.parse_args(argv)

    # Dispatch to the appropriate handler.
    exit_code = args.func(args)
    return exit_code

if __name__ == "__main__":
    sys.exit(main())

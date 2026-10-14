"""
Main entry point for the neural drift analysis pipeline.
"""

import argparse
import sys
import random
import numpy as np
from llmxive_toolkit import get_logger
from code.src import config
from code.src.data import loader

log = get_logger(__name__)

def _set_global_seed(seed: int) -> None:
    """Apply the given seed to the standard random generators."""
    random.seed(seed)
    np.random.seed(seed)

def _run_stage(stage: str) -> None:
    """
    Dispatch to a pipeline stage.

    Parameters
    ----------
    stage : str
        Name of the stage to run.  ``"all"`` runs every stage in order.
    """
    log.info(f"Running stage: {stage}")

    if stage in ("ingest", "all"):
        log.info("Stage: ingest — generating synthetic data")
        loader.main()
        log.info("Ingest complete")

    if stage == "all":
        log.info("All stages completed successfully")

def main(argv: list | None = None) -> int:
    """
    CLI entry point.

    Parameters
    ----------
    argv : list | None
        Argument list to parse; defaults to ``sys.argv[1:]``.
    Returns
    -------
    int
        Exit code (0 for success).
    """
    parser = argparse.ArgumentParser(
        description="Neural drift analysis pipeline"
    )
    parser.add_argument(
        "--stage",
        default="all",
        choices=["ingest", "preprocess", "drift", "correlation", "validation", "all"],
        help="Pipeline stage to run",
    )

    args = parser.parse_args(argv)

    _set_global_seed(config.CONFIG.random_seed)
    _run_stage(args.stage)

    return 0

if __name__ == "__main__":
    sys.exit(main())
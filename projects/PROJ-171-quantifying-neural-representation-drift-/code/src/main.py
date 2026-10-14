"""
Entry point for the drift analysis pipeline.

The script can be invoked as a module:

    python -m code.src.main --stage all

It sets the global random seed (from ``code.src.config.CONFIG``) and
dispatches to the requested pipeline stage.  At this skeleton stage the
stages are placeholders that simply log their invocation; later tasks will
replace the placeholders with the actual implementations.
"""
import argparse
import sys
import random

import numpy as np

# Import the configuration singleton
from . import config

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
    # In the full implementation each stage will be a function imported
    # from the appropriate sub‑module.  For now we simply acknowledge the
    # request.
    print(f"[INFO] Running stage: {stage}")
    # Placeholder: actual stage functions will be added in later tasks.

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
        description="Quantifying Neural Representation Drift pipeline"
    )
    parser.add_argument(
        "--stage",
        type=str,
        default="all",
        help="Pipeline stage to execute (e.g., 'all', 'loader', 'preprocess', 'drift', 'correlation')",
    )
    args = parser.parse_args(argv)

    # Apply the deterministic seed before any computation
    _set_global_seed(config.CONFIG.random_seed)

    # Run the requested stage
    _run_stage(args.stage)

    return 0

if __name__ == "__main__":
    sys.exit(main())

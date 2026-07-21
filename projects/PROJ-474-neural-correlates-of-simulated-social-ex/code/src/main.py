import os
import sys
import json
import logging
import argparse
from pathlib import Path

# Import step functions – they are defined in other modules.
from src.main import (
    run_download_qc_step,
    run_extract_connectivity_step,
    run_stats_viz_step,
)

def _parse_arguments() -> argparse.Namespace:
    """
    Parse command‑line arguments.

    The original implementation expected a positional ``step`` argument.
    The quick‑start guide, however, uses the ``--step`` flag.  To remain
    backward compatible we accept **both** forms.
    """
    parser = argparse.ArgumentParser(
        description="Run a single step of the neuro‑imaging pipeline."
    )
    # Positional argument (historical)
    parser.add_argument(
        "step_pos",
        nargs="?",
        help="Name of the step to run (positional, legacy).",
    )
    # New ``--step`` flag
    parser.add_argument(
        "--step",
        dest="step_flag",
        help="Name of the step to run (preferred flag).",
    )
    return parser.parse_args()

def main() -> int:
    """
    Entry‑point used by the run‑book. Returns an exit‑code compatible
    with the surrounding orchestration.
    """
    args = _parse_arguments()

    # Resolve which argument the user supplied.
    step = args.step_flag or args.step_pos
    if not step:
        print("Error: no step specified.", file=sys.stderr)
        return 1

    logger = logging.getLogger(__name__)
    logger.info(f"Running pipeline step: {step}")

    try:
        if step == "download_qc":
            run_download_qc_step()
        elif step == "extract_connectivity":
            run_extract_connectivity_step()
        elif step == "stats_viz":
            run_stats_viz_step()
        else:
            logger.error(f"Unknown step: {step}")
            return 1
    except Exception as exc:  # pragma: no cover – defensive
        logger.exception("Pipeline step failed")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
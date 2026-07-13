"""
code/main.py

Command‑line entry point for the project.  The original implementation
attempted to import ``analysis.correlation_main_runner`` which does not
exist as a top‑level package.  The corrected version imports the runner
from the proper ``code.analysis`` package.
"""

import argparse
import logging
import sys
from pathlib import Path

from logging_config import setup_logging, get_logger

# Fixed import – the runner lives in ``code.analysis.correlation_main_runner``.
from code.analysis.correlation_main_runner import main as run_analyze

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Project run‑book dispatcher")
    parser.add_argument(
        "--step",
        choices=["download_preprocess", "extract_metrics", "analyze", "viz_report"],
        required=True,
        help="Which pipeline step to execute",
    )
    parser.add_argument(
        "--subjects",
        type=int,
        default=0,
        help="Number of subjects to process (used by download/preprocess steps)",
    )
    return parser.parse_args()

def main() -> int:
    """
    Dispatches to the requested pipeline step.  Each step is implemented in
    its own module; this function only forwards control.
    Returns an exit‑code compatible with ``sys.exit``.
    """
    args = _parse_args()
    logger = get_logger()
    logger.info("Running step: %s", args.step)

    if args.step == "download_preprocess":
        # The download/preprocess module is not part of this task; we simply
        # import and run it if it exists.
        from code.data.download import main as download_main

        return download_main(subjects=args.subjects)
    elif args.step == "extract_metrics":
        from code.data.metrics import main as metrics_main

        return metrics_main()
    elif args.step == "analyze":
        # Run the correlation / PCA analysis pipeline.
        return run_analyze()
    elif args.step == "viz_report":
        from code.viz.scatter import main as scatter_main
        from code.viz.network import main as network_main
        from code.report.generate import main as report_main

        # Generate visualisations and the final report.
        scatter_main()
        network_main()
        report_main()
        return 0
    else:
        logger.error("Unknown step: %s", args.step)
        return 1

if __name__ == "__main__":
    sys.exit(main())

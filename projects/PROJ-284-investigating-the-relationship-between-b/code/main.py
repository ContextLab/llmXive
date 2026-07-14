"""
code/main.py

Main entry point for the research pipeline.
Orchestrates the download, preprocessing, metrics extraction, analysis, and reporting steps.
"""

import argparse
import sys
from pathlib import Path

from code.logging_config import get_logger
from code.data.download import download_pipeline
from code.data.metrics import main as metrics_main
from code.analysis.generate_full_metrics import main as generate_full_metrics_main
from code.analysis.correlations import main as correlations_main
from code.viz.scatter import main as scatter_main
from code.viz.network import main as network_main
from code.report.generate import main as report_main

logger = get_logger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description="Run the brain network analysis pipeline.")
    parser.add_argument(
        "--step",
        choices=["download_preprocess", "metrics", "generate_full_metrics", "correlations", "viz_report"],
        required=True,
        help="Which step of the pipeline to run."
    )
    parser.add_argument(
        "--subjects",
        type=int,
        default=50,
        help="Number of subjects to process (for download_preprocess step)."
    )
    parser.add_argument(
        "--input",
        type=str,
        help="Input file path for visualization steps."
    )
    parser.add_argument(
        "--x",
        type=str,
        help="X-axis column name for visualization."
    )
    parser.add_argument(
        "--y",
        type=str,
        help="Y-axis column name for visualization."
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path for visualization."
    )
    parser.add_argument(
        "--x-label",
        type=str,
        help="X-axis label for visualization."
    )
    parser.add_argument(
        "--y-label",
        type=str,
        help="Y-axis label for visualization."
    )
    parser.add_argument(
        "--title",
        type=str,
        help="Plot title for visualization."
    )
    return parser.parse_args()


def run_pipeline(step: str, subjects: int = 50):
    """Run the specified pipeline step."""
    logger.info(f"Running pipeline step: {step}")
    
    if step == "download_preprocess":
        download_pipeline(subjects)
    elif step == "metrics":
        metrics_main()
    elif step == "generate_full_metrics":
        generate_full_metrics_main()
    elif step == "correlations":
        correlations_main()
    elif step == "viz_report":
        # Visualization step requires additional arguments
        args = parse_args()
        if not all([args.input, args.x, args.y, args.output]):
            logger.error("Visualization step requires --input, --x, --y, and --output arguments.")
            sys.exit(1)
        scatter_main(
            input_file=args.input,
            x_col=args.x,
            y_col=args.y,
            output_file=args.output,
            x_label=args.x_label,
            y_label=args.y_label,
            title=args.title
        )
    else:
        logger.error(f"Unknown step: {step}")
        sys.exit(1)


def main():
    args = parse_args()
    run_pipeline(args.step, args.subjects)


if __name__ == "__main__":
    main()
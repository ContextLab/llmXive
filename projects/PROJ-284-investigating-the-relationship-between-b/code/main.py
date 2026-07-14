"""Main pipeline orchestrator."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from logging_config import get_logger
from data.download import download_pipeline
from data.metrics import main as metrics_main
from analysis.correlations import main as correlations_main
from report.generate import main as report_main
from viz.scatter import main as scatter_main
from viz.network import main as network_main

logger = get_logger(__name__)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Brain network analysis pipeline")
    parser.add_argument(
        "--step",
        choices=["download_preprocess", "metrics", "correlations", "viz_report"],
        default="download_preprocess",
        help="Pipeline step to run"
    )
    parser.add_argument(
        "--subjects",
        type=int,
        default=50,
        help="Number of subjects to process"
    )
    return parser.parse_args()


def run_pipeline(step: str, subjects: int = 50) -> None:
    """Run specified pipeline step."""
    logger.info(f"Running pipeline step: {step}")

    try:
        if step == "download_preprocess":
            logger.info(f"Downloading and preprocessing {subjects} subjects")
            download_pipeline(subjects)
            logger.info("Download and preprocessing complete")

        elif step == "metrics":
            logger.info("Extracting network metrics")
            metrics_main()
            logger.info("Metrics extraction complete")

        elif step == "correlations":
            logger.info("Running correlation analysis")
            correlations_main()
            logger.info("Correlation analysis complete")

        elif step == "viz_report":
            logger.info("Generating visualizations and report")
            correlations_main()  # Ensure full_metrics exists
            scatter_main()
            network_main()
            report_main()
            logger.info("Visualization and report generation complete")

    except Exception as e:
        logger.error(f"Pipeline step {step} failed: {e}")
        raise


def main():
    """Main entry point."""
    args = parse_args()
    run_pipeline(args.step, args.subjects)


if __name__ == "__main__":
    main()
"""Main pipeline entry point."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from logging_config import get_logger
from data.download import download_pipeline
from data.metrics import main as metrics_main

logger = get_logger(__name__)

VALID_STEPS = [
    "download_preprocess",
    "metrics",
    "extract_metrics",   # alias for metrics
    "correlations",
    "analyze",           # alias for correlations
    "viz_report",
]


def parse_args():
    parser = argparse.ArgumentParser(description="Brain Network Pipeline")
    parser.add_argument(
        "--step",
        choices=VALID_STEPS,
        required=True,
        help="Pipeline step to run",
    )
    parser.add_argument(
        "--subjects",
        type=int,
        default=10,
        help="Number of subjects to process",
    )
    return parser.parse_args()


def run_pipeline(step: str, subjects: int = 10):
    """Run a pipeline step."""
    logger.info(f"Running step: {step} (subjects={subjects})")

    if step == "download_preprocess":
        download_pipeline(subjects)

    elif step in ("metrics", "extract_metrics"):
        metrics_main()

    elif step in ("correlations", "analyze"):
        import os
        os.makedirs("data/analysis", exist_ok=True)
        # Run correlation analysis if full_metrics.csv exists
        metrics_path = Path("data/analysis/full_metrics.csv")
        if not metrics_path.exists():
            # Try to generate it first
            logger.info("full_metrics.csv not found, running metrics step first")
            metrics_main()
        if metrics_path.exists():
            try:
                from analysis.correlations import main as correlations_main
                correlations_main()
            except Exception as e:
                logger.error(f"Correlation analysis failed: {e}")
                raise
        else:
            raise RuntimeError(
                "data/analysis/full_metrics.csv not found after metrics step"
            )

    elif step == "viz_report":
        try:
            from report.generate import main as report_main
            report_main()
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            raise

    else:
        raise ValueError(f"Unknown step: {step}")


def main():
    args = parse_args()
    run_pipeline(args.step, args.subjects)


if __name__ == "__main__":
    main()
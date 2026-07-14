"""
Main entry point for the research pipeline.
Orchestrates the execution of download, preprocessing, metrics extraction, and analysis steps.
"""
import argparse
import sys
from pathlib import Path

from code.logging_config import get_logger
from code.data.download import download_pipeline
from code.data.metrics import main as metrics_main
from code.analysis.correlations import main as correlations_main
from code.viz.scatter import main as scatter_main
from code.report.generate import main as report_main

logger = get_logger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description="llmXive Research Pipeline")
    parser.add_argument(
        "--step",
        type=str,
        required=True,
        choices=["download_preprocess", "metrics", "correlations", "viz_report"],
        help="Pipeline step to execute"
    )
    parser.add_argument(
        "--subjects",
        type=int,
        default=50,
        help="Number of subjects to process (for download/preview)"
    )
    return parser.parse_args()


def run_pipeline(step: str, subjects: int = 50):
    logger.log("run_pipeline", step=step, subjects=subjects)

    if step == "download_preprocess":
        # T012/T012a/T013a-T013c/T014/T015
        download_pipeline(subjects=subjects)
    
    elif step == "metrics":
        # T017/T020/T021/T022
        # This step handles atlas loading, time-series extraction, and metric calculation
        metrics_main()
    
    elif step == "correlations":
        # T023a/T023b/T024/T025
        # This step handles PCA, metric merging, and correlation analysis
        correlations_main()
    
    elif step == "viz_report":
        # T031/T032/T033
        # Visualization and report generation
        scatter_main()
        report_main()
    
    else:
        raise ValueError(f"Unknown step: {step}")

    logger.log("pipeline_step_complete", step=step)


def main():
    args = parse_args()
    try:
        run_pipeline(args.step, args.subjects)
        logger.log("pipeline_success")
    except Exception as e:
        logger.log("pipeline_failure", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()

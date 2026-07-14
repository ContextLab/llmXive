"""
Main entry point for the pipeline.
"""
import argparse
import sys
from pathlib import Path
import os
from code.logging_config import get_logger
from code.data.download import main as download_main
from code.data.metrics import main as metrics_main
from code.analysis.correlations import main as correlations_main
from code.analysis.pca_runner import main as pca_main
from code.viz.scatter import main as viz_main
from code.report.generate import main as report_main

logger = get_logger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="Brain Network Dynamics Pipeline")
    parser.add_argument("--step", type=str, required=True, help="Pipeline step to run")
    parser.add_argument("--subjects", type=int, default=50, help="Number of subjects to process")
    return parser.parse_args()

def run_pipeline(step: str, subjects: int):
    logger.log("run_pipeline", step=step, subjects=subjects)

    if step == "download_preprocess":
        download_main()
    elif step == "extract_metrics":
        metrics_main()
    elif step == "analyze":
        correlations_main()
        pca_main()
    elif step == "viz_report":
        viz_main()
        report_main()
    else:
        logger.log("run_pipeline", status="failed", error=f"Unknown step: {step}")

def main():
    args = parse_args()
    run_pipeline(args.step, args.subjects)

if __name__ == "__main__":
    main()

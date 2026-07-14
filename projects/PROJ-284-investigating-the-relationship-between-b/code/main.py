"""
Main entry point for the pipeline.
Handles step execution: download_preprocess, metrics, correlations, viz_report.
"""
import argparse
import sys
from pathlib import Path
import os
from code.logging_config import get_logger
from code.data.download import main as download_main
from code.data.metrics import main as metrics_main
from code.analysis.correlations import main as correlations_main
from code.viz.scatter import main as viz_main

logger = get_logger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="Brain Network Dynamics Pipeline")
    parser.add_argument(
        "--step",
        choices=["download_preprocess", "metrics", "correlations", "viz_report"],
        required=True,
        help="Pipeline step to execute"
    )
    parser.add_argument(
        "--subjects",
        type=int,
        default=50,
        help="Number of subjects to process (for download_preprocess)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output directory override"
    )
    return parser.parse_args()

def run_pipeline(step: str, subjects: int = 50):
    logger.log("pipeline_start", {"step": step, "subjects": subjects})
    
    if step == "download_preprocess":
        # T012/T012a logic: Fetch data (real or synthetic validation)
        # We call the download module which handles the logic
        download_main(subjects=subjects)
        
    elif step == "metrics":
        # T017/T020/T021/T022 logic: Extract metrics
        metrics_main()
        
    elif step == "correlations":
        # T023a/T023b/T024/T025 logic: PCA, Merge, Correlations
        correlations_main()
        
    elif step == "viz_report":
        # T031/T032/T033 logic: Visualization
        viz_main()
    else:
        logger.log("pipeline_error", {"message": "Invalid step"})
        sys.exit(1)
        
    logger.log("pipeline_complete", {"step": step})

def main():
    args = parse_args()
    run_pipeline(args.step, args.subjects)

if __name__ == "__main__":
    main()

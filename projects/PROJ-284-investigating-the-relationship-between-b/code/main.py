import argparse
import sys
from pathlib import Path
from code.logging_config import get_logger
from code.data.download import download_pipeline
from code.data.metrics import main as metrics_main
from code.analysis.correlations import main as correlations_main
from code.viz.scatter import main as viz_scatter_main
from code.report.generate import main as report_main

logger = get_logger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="llmXive Research Pipeline")
    parser.add_argument("--step", required=True, choices=["download_preprocess", "metrics", "correlations", "viz_report"],
                        help="Pipeline step to execute")
    parser.add_argument("--subjects", type=int, default=50, help="Number of subjects to process (for download_preprocess)")
    return parser.parse_args()

def run_pipeline(step: str, subjects: int):
    logger.log("run_pipeline", step=step, subjects=subjects)
    
    if step == "download_preprocess":
        # Create a dummy subject list for testing if not downloading real data
        # In a real run, this would fetch from HCP
        subject_ids = [f"sub-{i:04d}" for i in range(subjects)]
        download_pipeline(subjects=subject_ids)
    elif step == "metrics":
        metrics_main()
    elif step == "correlations":
        correlations_main()
    elif step == "viz_report":
        # Ensure analysis data exists before viz
        viz_scatter_main()
        report_main()
    else:
        raise ValueError(f"Unknown step: {step}")

def main():
    args = parse_args()
    try:
        result = run_pipeline(args.step, args.subjects)
        logger.log("main", step=args.step, status="success")
    except Exception as e:
        logger.log("main", step=args.step, status="failed", error=str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()

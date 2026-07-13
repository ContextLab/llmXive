"""
Main entry point for the pipeline.
"""
import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.logging_config import setup_logging, get_logger
from code.analysis.correlation_main_runner import main as run_analyze
from code.data.download import main as run_download
from code.data.preprocess import main as run_preprocess
from code.data.metrics import main as run_metrics
from code.viz.scatter import main as run_viz_scatter
from code.viz.network import main as run_viz_network
from code.report.generate import main as run_report

logger = get_logger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="llmXive Science Pipeline")
    parser.add_argument(
        "--step",
        type=str,
        choices=["download", "preprocess", "metrics", "analyze", "viz", "report", "all"],
        required=True,
        help="Pipeline step to execute"
    )
    parser.add_argument(
        "--subjects",
        type=int,
        default=10,
        help="Number of subjects to process"
    )
    return parser.parse_args()

def run_pipeline(step: str, num_subjects: int):
    logger.log("run_pipeline", step=step, subjects=num_subjects)
    
    if step == "download":
        run_download(num_subjects)
    elif step == "preprocess":
        run_preprocess(num_subjects)
    elif step == "metrics":
        run_metrics(num_subjects)
    elif step == "analyze":
        # This triggers T023a (PCA) and T023b (Merge/Save)
        run_analyze()
    elif step == "viz":
        run_viz_scatter()
        run_viz_network()
    elif step == "report":
        run_report()
    elif step == "all":
        run_download(num_subjects)
        run_preprocess(num_subjects)
        run_metrics(num_subjects)
        run_analyze()
        run_viz_scatter()
        run_viz_network()
        run_report()

def main():
    setup_logging()
    args = parse_args()
    try:
        run_pipeline(args.step, args.subjects)
        logger.log("main", status="success")
    except Exception as e:
        logger.log("main", status="failed", error=str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
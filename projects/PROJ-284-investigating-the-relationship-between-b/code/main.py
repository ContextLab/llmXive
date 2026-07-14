"""
Main Pipeline Controller.
Orchestrates the steps: download, preprocess, metrics, analyze, viz, report.
"""
import argparse
import sys
from pathlib import Path
from code.logging_config import setup_logging, get_logger
from code.analysis.correlation_main_runner import main as run_analyze

logger = get_logger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="llmXive Research Pipeline")
    parser.add_argument("--step", type=str, required=True,
                        choices=["download", "preprocess", "metrics", "analyze", "viz", "report", "all"],
                        help="Pipeline step to execute")
    parser.add_argument("--subjects", type=int, default=50, help="Number of subjects to process")
    return parser.parse_args()

def run_pipeline(step: str, subjects: int):
    logger.info(f"Starting pipeline step: {step} with {subjects} subjects")
    
    if step == "download":
        from code.data.download import main
        main()
    elif step == "preprocess":
        from code.data.preprocess import main
        main()
    elif step == "metrics":
        from code.data.metrics import main
        main()
    elif step == "analyze":
        # T028: This step includes dynamic batch sizing logic
        run_analyze()
    elif step == "viz":
        from code.viz.scatter import main as viz_scatter
        from code.viz.network import main as viz_network
        viz_scatter()
        viz_network()
    elif step == "report":
        from code.report.generate import main
        main()
    elif step == "all":
        run_pipeline("download", subjects)
        run_pipeline("preprocess", subjects)
        run_pipeline("metrics", subjects)
        run_pipeline("analyze", subjects)
        run_pipeline("viz", subjects)
        run_pipeline("report", subjects)

def main():
    args = parse_args()
    setup_logging()
    run_pipeline(args.step, args.subjects)

if __name__ == "__main__":
    main()
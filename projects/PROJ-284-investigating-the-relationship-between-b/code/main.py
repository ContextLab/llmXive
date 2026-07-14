"""
Main entry point for the research pipeline.
Orchestrates steps: download_preprocess, metrics, correlations, viz_report.
"""
import argparse
import sys
from pathlib import Path
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.logging_config import get_logger

from code.data.download import main as download_main
from code.data.metrics import main as metrics_main
from code.analysis.correlations import main as correlations_main
from code.report.generate import main as report_main
from code.viz.scatter import main as scatter_main
from code.viz.network import main as network_main

logger = get_logger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="Brain Network Dynamics Pipeline")
    parser.add_argument("--step", type=str, required=True,
                        choices=["download_preprocess", "metrics", "correlations", "viz_report"],
                        help="Pipeline step to execute")
    parser.add_argument("--subjects", type=int, default=50, help="Number of subjects")
    parser.add_argument("--output", type=str, default="data/analysis", help="Output directory")
    return parser.parse_args()

def run_pipeline(step: str, subjects: int = 50, output: str = "data/analysis"):
    logger.log("run_pipeline", step=step, subjects=subjects)
    
    if step == "download_preprocess":
        # Execute download and synthetic validation
        # We pass subjects via environment or override main logic if needed
        # For now, we assume download_main handles defaults or we patch it
        import os
        os.environ["SUBJECTS"] = str(subjects)
        download_main()
        
    elif step == "metrics":
        metrics_main()
        
    elif step == "correlations":
        correlations_main()
        
    elif step == "viz_report":
        # Generate plots and report
        scatter_main()
        network_main()
        report_main()
    else:
        logger.log("pipeline_step_unknown", {"step": step})
        raise ValueError(f"Unknown step: {step}")

    logger.log("pipeline_step_complete", {"step": step})

def main():
    args = parse_args()
    try:
        run_pipeline(args.step, args.subjects, args.output)
        logger.log("pipeline_complete", step=args.step)
    except Exception as e:
        logger.log("pipeline_error", error=str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
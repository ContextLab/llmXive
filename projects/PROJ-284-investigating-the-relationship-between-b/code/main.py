import argparse
import sys
from pathlib import Path
from code.logging_config import get_logger
from code.data.download import download_pipeline
from code.data.metrics import main as metrics_main
from code.analysis.run_analysis import main as analysis_main
from code.viz.scatter import main as viz_scatter_main
from code.viz.network import main as viz_network_main
from code.report.generate import main as report_main

logger = get_logger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="Brain Network Dynamics Pipeline")
    parser.add_argument("--step", type=str, required=True, 
                        choices=["download_preprocess", "metrics", "correlations", "viz_report"],
                        help="Pipeline step to execute")
    parser.add_argument("--subjects", type=int, default=50, help="Number of subjects to process")
    return parser.parse_args()

def run_pipeline(step: str, subjects: int):
    logger.log("run_pipeline", step=step, subjects=subjects)
    
    if step == "download_preprocess":
        # T012-T015: Download and preprocess
        # Note: Full preprocessing requires FSL/AFNI. This step may run in validation mode on CI.
        download_pipeline(subjects=subjects)
    elif step == "metrics":
        # T017, T020-T022: Extract metrics
        metrics_main(subjects=subjects)
    elif step == "correlations":
        # T023a, T023b, T024, T025: PCA, merge, correlations
        analysis_main()
    elif step == "viz_report":
        # T031-T033: Visualization and reporting
        viz_scatter_main()
        viz_network_main()
        report_main()
    else:
        logger.error(f"Unknown step: {step}")
        return 1
    
    return 0

def main():
    args = parse_args()
    result = run_pipeline(args.step, args.subjects)
    sys.exit(result)

if __name__ == "__main__":
    main()

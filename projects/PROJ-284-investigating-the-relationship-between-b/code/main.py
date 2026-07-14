"""
Main pipeline orchestrator.
Handles command-line arguments and dispatches to pipeline steps.
"""
import argparse
import sys
from pathlib import Path
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.logging_config import get_logger

logger = get_logger(__name__)

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Brain Network Dynamics Analysis Pipeline")
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
        help="Number of subjects to process"
    )
    parser.add_argument(
        "--correlations",
        type=str,
        default=None,
        help="Specific correlations to compute"
    )
    parser.add_argument(
        "--power",
        type=str,
        default=None,
        help="Power analysis configuration"
    )
    parser.add_argument(
        "--plots",
        type=str,
        default=None,
        help="Plots to generate"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output directory"
    )
    return parser.parse_args()

def run_pipeline(step: str, subjects: int = 50):
    """Run the specified pipeline step."""
    logger.log("pipeline_step_start", {"step": step, "subjects": subjects})

    if step == "download_preprocess":
        from code.data.download import main as download_main
        download_main()

    elif step == "metrics":
        from code.data.metrics import main as metrics_main
        metrics_main()

    elif step == "correlations":
        from code.analysis.correlations import main as correlations_main
        correlations_main()

    elif step == "viz_report":
        from code.report.generate import main as report_main
        report_main()

    else:
        logger.log("pipeline_step_unknown", {"step": step})
        raise ValueError(f"Unknown step: {step}")

    logger.log("pipeline_step_complete", {"step": step})

def main():
    """Main entry point."""
    args = parse_args()

    try:
        run_pipeline(args.step, args.subjects)
    except Exception as e:
        logger.log("pipeline_error", {"error": str(e), "step": args.step})
        sys.exit(1)

if __name__ == "__main__":
    main()
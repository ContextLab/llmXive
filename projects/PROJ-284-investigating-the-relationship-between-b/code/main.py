"""
Main entry point for the research pipeline.
Handles command-line arguments and orchestrates pipeline steps.
"""
import argparse
import sys
from pathlib import Path
from code.logging_config import get_logger

logger = get_logger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Brain Network Dynamics Research Pipeline"
    )
    
    parser.add_argument(
        "--step",
        type=str,
        choices=["download_preprocess", "metrics", "correlations", "viz_report"],
        required=True,
        help="Pipeline step to execute"
    )
    
    parser.add_argument(
        "--subjects",
        type=int,
        default=None,
        help="Number of subjects to process (for download_preprocess step)"
    )
    
    parser.add_argument(
        "--correlations",
        type=str,
        default="data/analysis/correlations.csv",
        help="Path to correlation results file"
    )
    
    parser.add_argument(
        "--power",
        type=str,
        default="data/analysis/power_analysis.csv",
        help="Path to power analysis results file"
    )
    
    parser.add_argument(
        "--plots",
        type=str,
        default="figures/",
        help="Directory for output plots"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default="reports/",
        help="Directory for output reports"
    )
    
    return parser.parse_args()

def run_pipeline(step: str, subjects: int = None, **kwargs):
    """
    Execute a specific pipeline step.
    
    Args:
        step: Pipeline step name
        subjects: Number of subjects to process
        **kwargs: Additional arguments for specific steps
    """
    if step == "download_preprocess":
        from code.data.download import download_pipeline
        logger.log("pipeline_step_start", step=step, subjects=subjects)
        download_pipeline(subject_count=subjects)
        logger.log("pipeline_step_complete", step=step)
    
    elif step == "metrics":
        from code.data.metrics import main as metrics_main
        logger.log("pipeline_step_start", step=step)
        metrics_main()
        logger.log("pipeline_step_complete", step=step)
    
    elif step == "correlations":
        from code.analysis.correlations import main as correlations_main
        logger.log("pipeline_step_start", step=step)
        correlations_main()
        logger.log("pipeline_step_complete", step=step)
    
    elif step == "viz_report":
        # Check for required files
        corr_path = kwargs.get('correlations', 'data/analysis/correlations.csv')
        if not Path(corr_path).exists():
            logger.log("viz_report_error", error=f"Correlation results file not found: {corr_path}")
            print(f"Error: Correlation results file not found: {corr_path}")
            print("Please run the correlation analysis first (T024, T025)")
            sys.exit(1)
        
        from code.viz.scatter import main as scatter_main
        from code.viz.network import main as network_main
        from code.report.generate import main as report_main
        
        logger.log("pipeline_step_start", step=step)
        scatter_main()
        network_main()
        report_main()
        logger.log("pipeline_step_complete", step=step)
    
    else:
        raise ValueError(f"Unknown step: {step}")

def main():
    """Main entry point."""
    args = parse_args()
    
    try:
        run_pipeline(
            step=args.step,
            subjects=args.subjects,
            correlations=args.correlations,
            power=args.power,
            plots=args.plots,
            output=args.output
        )
    except Exception as e:
        logger.log("pipeline_error", step=args.step, error=str(e))
        print(f"Error in pipeline step '{args.step}': {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

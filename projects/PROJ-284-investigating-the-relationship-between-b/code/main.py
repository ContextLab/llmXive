"""
Main entry point for the pipeline.
Orchestrates the execution of download, preprocess, metrics, analysis, and viz steps.
"""
import argparse
import sys
from pathlib import Path

# Add code to path
sys.path.insert(0, str(Path(__file__).parent))

from code.logging_config import get_logger
from code.analysis.correlation_main_runner import main as run_analyze

logger = get_logger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="llmXive Science Pipeline")
    parser.add_argument("--step", type=str, required=True, choices=[
        "download_preprocess", "extract_metrics", "analyze", "viz_report"
    ], help="Pipeline step to execute")
    parser.add_argument("--subjects", type=int, default=50, help="Number of subjects to process")
    return parser.parse_args()

def run_pipeline(step: str, subjects: int = 50):
    logger.log("pipeline_start", step=step, subjects=subjects)
    
    if step == "download_preprocess":
        from code.data.download import main as download_main
        from code.data.preprocess import main as preprocess_main
        download_main()
        preprocess_main()
    
    elif step == "extract_metrics":
        from code.data.metrics import main as metrics_main
        metrics_main()
    
    elif step == "analyze":
        # Run PCA and Correlations
        from code.analysis.pca_runner import main as pca_main
        from code.analysis.create_full_metrics import main as create_full_main
        from code.analysis.correlations import main as corr_main
        
        try:
            pca_main()
        except Exception as e:
            logger.log("pca_failed", reason=str(e))
        
        try:
            create_full_main()
        except Exception as e:
            logger.log("create_full_metrics_failed", reason=str(e))
        
        try:
            corr_main()
        except Exception as e:
            logger.log("correlation_failed", reason=str(e))
    
    elif step == "viz_report":
        from code.viz.scatter import main as scatter_main
        from code.viz.network import main as network_main
        from code.report.generate import main as report_main
        scatter_main()
        network_main()
        report_main()
    
    logger.log("pipeline_end", step=step)

def main():
    args = parse_args()
    run_pipeline(args.step, args.subjects)

if __name__ == "__main__":
    main()

import os
import sys
import argparse
import logging
from pathlib import Path
from logging_config import setup_logging, get_logger
from data.download import main as download_main
from data.metrics import main as metrics_main
from analysis.correlations import main as correlations_main
from viz.scatter import main as scatter_main
from viz.network import main as network_main
from report.generate import main as report_main

logger = get_logger(__name__)

def run_download_preprocess(subjects=None):
    """
    Run data download and preprocessing pipeline.
    """
    logger.info("Running download and preprocessing pipeline")
    success = download_main()
    if not success:
        logger.error("Download pipeline failed")
        return False
    return True

def run_extract_metrics(subjects=None):
    """
    Extract network metrics from preprocessed data.
    """
    logger.info("Running metrics extraction")
    success = metrics_main()
    if not success:
        logger.error("Metrics extraction failed")
        return False
    return True

def run_analyze():
    """
    Run correlation analysis and PCA.
    """
    logger.info("Running analysis")
    success = correlations_main()
    if not success:
        logger.error("Analysis failed")
        return False
    return True

def run_viz_report():
    """
    Generate visualizations and report.
    """
    logger.info("Running visualization and report generation")
    success_scatter = scatter_main()
    success_network = network_main()
    success_report = report_main()
    
    if not (success_scatter and success_network and success_report):
        logger.error("Visualization or report generation failed")
        return False
    return True

def main():
    """
    Main entry point for the pipeline.
    """
    parser = argparse.ArgumentParser(description="Brain Network Dynamics Analysis Pipeline")
    parser.add_argument('--step', type=str, required=True, 
                      choices=['download_preprocess', 'extract_metrics', 'analyze', 'viz_report'],
                      help='Pipeline step to run')
    parser.add_argument('--subjects', type=int, default=None,
                      help='Number of subjects to process')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    if args.step == 'download_preprocess':
        success = run_download_preprocess()
    elif args.step == 'extract_metrics':
        success = run_extract_metrics()
    elif args.step == 'analyze':
        success = run_analyze()
    elif args.step == 'viz_report':
        success = run_viz_report()
    else:
        logger.error(f"Unknown step: {args.step}")
        return False
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

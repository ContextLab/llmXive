"""
High-level analysis orchestration module.
Provides unified interface for running all analysis pipelines.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.correlations import run_correlation_pipeline
from analysis.lme_model import run_lme_part3_lrt_and_output
from analysis.metrics import run_metrics_pipeline
from config import load_config

logger = logging.getLogger(__name__)

def load_analysis_data(config: Dict[str, Any]) -> Dict[str, Any]:
    """Load all necessary data for analysis."""
    return {
        'config': config,
        'processed_dir': Path(config['paths']['processed_data']),
        'results_dir': Path(config['paths']['results'])
    }

def run_correlation_analysis(config: Dict[str, Any]):
    """Run correlation analysis pipeline."""
    logger.info("Running correlation analysis...")
    run_correlation_pipeline(config)

def run_mixed_effects_analysis(config: Dict[str, Any]):
    """Run mixed effects model analysis."""
    logger.info("Running mixed effects analysis...")
    run_lme_part3_lrt_and_output(config)

def run_full_analysis_pipeline(config: Dict[str, Any]):
    """Run the complete analysis pipeline."""
    logger.info("Starting full analysis pipeline...")
    
    # Run metrics extraction
    run_metrics_pipeline(config)
    
    # Run correlation analysis
    run_correlation_analysis(config)
    
    # Run mixed effects analysis
    run_mixed_effects_analysis(config)
    
    logger.info("Full analysis pipeline completed.")

def main():
    """Main entry point for analysis."""
    parser = argparse.ArgumentParser(description="Run analysis pipelines")
    parser.add_argument("--config", type=str, default="code/config.yaml")
    parser.add_argument("--mode", type=str, default="full", 
                      choices=["correlation", "lme", "full"],
                      help="Analysis mode to run")
    args = parser.parse_args()
    
    config = load_config(Path(args.config))
    
    if args.mode == "correlation":
        run_correlation_analysis(config)
    elif args.mode == "lme":
        run_mixed_effects_analysis(config)
    else:
        run_full_analysis_pipeline(config)

if __name__ == "__main__":
    main()
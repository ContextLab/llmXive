"""
Main CLI entry point for the llmXive statistical robustness pipeline.

Orchestrates the full workflow:
1. Download and clean datasets
2. Inject errors (synthetic and real)
3. Run statistical analyses
4. Visualize results
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Ensure project root is in path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from download import main as download_main
from inject import main as inject_main
from simulate import main as simulate_main
from analyze import main as analyze_main
from visualize import main as visualize_main

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROJECT_ROOT / 'logs' / 'pipeline.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Run the full statistical robustness evaluation pipeline.'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config/pipeline_config.yaml',
        help='Path to the pipeline configuration file.'
    )
    parser.add_argument(
        '--skip-download',
        action='store_true',
        help='Skip the download and clean step.'
    )
    parser.add_argument(
        '--skip-inject',
        action='store_true',
        help='Skip the error injection step.'
    )
    parser.add_argument(
        '--skip-simulate',
        action='store_true',
        help='Skip the synthetic data generation step.'
    )
    parser.add_argument(
        '--skip-analyze',
        action='store_true',
        help='Skip the statistical analysis step.'
    )
    parser.add_argument(
        '--skip-visualize',
        action='store_true',
        help='Skip the visualization step.'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Print planned steps without executing them.'
    )
    return parser.parse_args()

def run_pipeline(args):
    """Execute the pipeline stages based on arguments."""
    logger.info("Starting Statistical Robustness Pipeline")
    logger.info(f"Configuration: {args.config}")
    
    if args.dry_run:
        logger.info("DRY RUN MODE - No actions will be executed")
        steps = []
        if not args.skip_download:
            steps.append("Download & Clean Datasets")
        if not args.skip_inject:
            steps.append("Inject Errors")
        if not args.skip_simulate:
            steps.append("Generate Synthetic Data")
        if not args.skip_analyze:
            steps.append("Run Statistical Analysis")
        if not args.skip_visualize:
            steps.append("Generate Visualizations")
        
        for i, step in enumerate(steps, 1):
            logger.info(f"{i}. {step}")
        return
    
    # Ensure output directories exist
    output_dirs = [
        'data/raw', 'data/raw/cleaned', 'data/corrupted',
        'data/corrupted/synthetic_grid', 'data/corrupted/null_hypothesis',
        'results/raw_metrics', 'results/aggregated_metrics', 'results/plots',
        'results/tables', 'state', 'logs'
    ]
    for dir_name in output_dirs:
        Path(dir_name).mkdir(parents=True, exist_ok=True)
    
    # Step 1: Download and Clean
    if not args.skip_download:
        logger.info("Step 1: Downloading and cleaning datasets...")
        try:
            # We need to pass config to the download module
            # Assuming the modules handle their own config loading or we pass args
            # For now, we rely on the modules' main functions to handle config
            # If they require specific args, we'd need to refactor slightly
            download_main() 
            logger.info("Download and clean step completed.")
        except Exception as e:
            logger.error(f"Download step failed: {e}")
            if not args.skip_analyze: # Decide if we continue or fail fast
                logger.warning("Continuing despite download failure...")
            else:
                return
    else:
        logger.info("Step 1: Skipped (download).")
    
    # Step 2: Inject Errors
    if not args.skip_inject:
        logger.info("Step 2: Injecting errors into datasets...")
        try:
            inject_main()
            logger.info("Error injection step completed.")
        except Exception as e:
            logger.error(f"Injection step failed: {e}")
            if not args.skip_analyze:
                logger.warning("Continuing despite injection failure...")
            else:
                return
    else:
        logger.info("Step 2: Skipped (inject).")
    
    # Step 3: Simulate (Synthetic/Null Data)
    if not args.skip_simulate:
        logger.info("Step 3: Generating synthetic and null-hypothesis datasets...")
        try:
            simulate_main()
            logger.info("Simulation step completed.")
        except Exception as e:
            logger.error(f"Simulation step failed: {e}")
            if not args.skip_analyze:
                logger.warning("Continuing despite simulation failure...")
            else:
                return
    else:
        logger.info("Step 3: Skipped (simulate).")
    
    # Step 4: Analyze
    if not args.skip_analyze:
        logger.info("Step 4: Running statistical analyses...")
        try:
            analyze_main()
            logger.info("Analysis step completed.")
        except Exception as e:
            logger.error(f"Analysis step failed: {e}")
            if not args.skip_visualize:
                logger.warning("Continuing despite analysis failure...")
            else:
                return
    else:
        logger.info("Step 4: Skipped (analyze).")
    
    # Step 5: Visualize
    if not args.skip_visualize:
        logger.info("Step 5: Generating visualizations...")
        try:
            visualize_main()
            logger.info("Visualization step completed.")
        except Exception as e:
            logger.error(f"Visualization step failed: {e}")
            return
    else:
        logger.info("Step 5: Skipped (visualize).")
    
    logger.info("Pipeline execution finished.")

def main():
    """Main entry point."""
    args = parse_args()
    run_pipeline(args)

if __name__ == '__main__':
    main()
import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

# Add code directory to path for imports
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from utils.config import load_config, ensure_directories
from analysis.threshold_sweep_aggregator import main as aggregate_sweep_results

def parse_args():
    parser = argparse.ArgumentParser(description="Main entry point for random matrix eigenvalue analysis")
    parser.add_argument('--config', type=str, default='code/config.json', help='Path to configuration file')
    parser.add_argument('--task', type=str, choices=['sweep_aggregate'], help='Task to execute')
    parser.add_argument('--input', type=str, help='Input file path (task dependent)')
    parser.add_argument('--output', type=str, help='Output file path (task dependent)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    return parser.parse_args()

def setup_logging(verbose=False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('data/logs/main_execution.log')
        ]
    )

def main():
    args = parse_args()
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    try:
        # Load configuration if provided
        if args.config and os.path.exists(args.config):
            config = load_config(args.config)
            ensure_directories(config)
            logger.info(f"Loaded configuration from {args.config}")
        else:
            logger.warning("No configuration file found, using defaults")

        # Execute requested task
        if args.task == 'sweep_aggregate':
            logger.info("Executing sweep aggregation task (T024)")
            # Override paths if provided via CLI
            if args.input:
                # This would require modifying the aggregator to accept CLI args
                # For now, we use default paths as defined in the task
                logger.warning("Input path override not implemented for this task. Using default.")
            if args.output:
                logger.warning("Output path override not implemented for this task. Using default.")
            
            return aggregate_sweep_results()
        
        else:
            logger.error(f"Unknown task: {args.task}")
            return 1

    except Exception as e:
        logger.error(f"Execution failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
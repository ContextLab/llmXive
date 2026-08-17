import argparse
import logging
import sys
from pathlib import Path
from utils.logging import setup_logging, get_logger
from config import get_project_root, ensure_directories

logger = get_logger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='llmXive Research Pipeline')
    parser.add_argument('--stage', type=str, choices=['setup', 'process_stimuli', 'process_data', 'analyze', 'all'],
                      default='all', help='Pipeline stage to run')
    parser.add_argument('--null-effect', action='store_true',
                      help='Use synthetic data for CI/testing')
    parser.add_argument('--verbose', action='store_true',
                      help='Enable verbose logging')
    return parser.parse_args()

def main():
    """Main entry point for the pipeline."""
    args = parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level=log_level)
    
    # Ensure directories exist
    ensure_directories()
    
    root = get_project_root()
    logger.info(f"Project root: {root}")
    
    if args.stage in ['setup', 'all']:
        logger.info("Stage: Setup - Directories created")
    
    if args.stage in ['process_stimuli', 'all']:
        logger.info("Stage: Process Stimuli")
        from stimuli.process import main as process_stimuli_main
        process_stimuli_main()
    
    if args.stage in ['process_data', 'all']:
        logger.info("Stage: Process Data")
        from data.load import main as load_main
        load_main()
        from data.process import main as process_data_main
        process_data_main()
    
    if args.stage in ['analyze', 'all']:
        logger.info("Stage: Analyze")
        from analysis.permutation import main as analyze_main
        analyze_main()
    
    logger.info("Pipeline completed successfully")

if __name__ == "__main__":
    main()

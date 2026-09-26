import argparse
import sys
import logging
from pathlib import Path
from config import Config
from utils import setup_logging

def run_stage(stage_name: str, config: Config) -> None:
    """Run a specific stage of the pipeline."""
    logger = logging.getLogger(__name__)
    logger.info(f"Running stage: {stage_name}")
    
    # Import stage-specific modules
    if stage_name == "setup_dirs":
        from setup_dirs import main as setup_dirs_main
        setup_dirs_main()
    elif stage_name == "data_setup":
        from data_setup import main as data_setup_main
        data_setup_main()
    elif stage_name == "setup_dependencies":
        from setup_dependencies import main as setup_deps_main
        setup_deps_main()
    elif stage_name == "linting_config":
        from linting_config import main as linting_config_main
        linting_config_main()
    else:
        logger.error(f"Unknown stage: {stage_name}")
        sys.exit(1)

def main():
    """Main entry point for the pipeline."""
    parser = argparse.ArgumentParser(description="Avian Song Variation Prediction Pipeline")
    parser.add_argument('--stage', type=str, required=True, help='Stage to run')
    parser.add_argument('--config', type=str, default=None, help='Path to config file')
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Load configuration
    config = Config(args.config) if args.config else Config()
    
    # Run the specified stage
    run_stage(args.stage, config)

if __name__ == "__main__":
    main()
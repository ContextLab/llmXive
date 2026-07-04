"""
Main entry point for the Lorentz Violation Testing Pipeline.

This script initializes the environment, loads configuration, enforces
random seeds for reproducibility, and sets up logging. It serves as the
central orchestrator for the analysis pipeline.
"""

import sys
from pathlib import Path

# Ensure the project root is in the path for relative imports if run directly
# However, standard practice in this project is to run from root with PYTHONPATH set
# or via a runner script. We assume standard execution context.

from code.config import load_config, enforce_seeds
from code.utils.logging import setup_logger

def main():
    """
    Entry point for the pipeline.

    1. Loads configuration from 'config.yaml'.
    2. Enforces random seeds for reproducibility.
    3. Initializes the logging system.
    4. (Future) Executes pipeline stages.
    """
    try:
        # Load configuration
        config_path = Path("config.yaml")
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        config = load_config(config_path)
        
        # Enforce seeds for reproducibility
        enforce_seeds(config)
        
        # Setup logging based on config
        logger = setup_logger(config)
        
        logger.info("Lorentz Violation Testing Pipeline started.")
        logger.info(f"Configuration loaded from: {config_path}")
        logger.info(f"Random seeds enforced: {config.get('seeds', {})}")
        
        # TODO: Add pipeline execution logic here as other tasks are completed
        # Example:
        # from code.data.downloader import run_download_pipeline
        # from code.analysis.inference import run_inference
        
        logger.info("Pipeline initialization complete. Ready for execution.")
        
    except FileNotFoundError as e:
        print(f"Critical Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        # Catch-all for unexpected errors during startup
        print(f"Unexpected error during pipeline startup: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
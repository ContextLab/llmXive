"""
Main entry point for the llmXive pipeline.
Configures global logging (JSON rotating file) and redirects stdout/stderr.
"""
import sys
import os

# Ensure project root is in path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from logger import configure_global_logging, get_logger

def main() -> int:
    """
    Main execution function.
    Initializes logging and redirects stdout/stderr before any other processing.
    """
    # Initialize logging and redirect stdout/stderr
    logger = configure_global_logging()
    logger.info("llmXive pipeline started.")

    try:
        # Placeholder for actual pipeline execution logic
        # This would typically orchestrate the renderer, agent, and scorer modules
        logger.info("Pipeline execution placeholder.")
        
        # Example of using the logger
        logger.info("Task T008: Logger configured successfully.")
        
        return 0
    except Exception as e:
        logger.exception("Pipeline execution failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

import sys
import logging
from pathlib import Path
from utils.logger import get_logger
from utils.profiler import run_profiler
from main import main as pipeline_main

logger = get_logger(__name__)

def main():
    """
    Orchestrates the profiling of the entire pipeline.
    """
    logger.info("Initializing pipeline profiler...")
    
    # Run the profiler on the main pipeline function
    # Passing empty args/kwargs as the main function handles its own CLI parsing if needed
    # or we can pass specific args if the pipeline supports them.
    # For this task, we assume the pipeline runs with default config/mock data if no args.
    success = run_profiler(
        pipeline_func=pipeline_main,
        args=(), 
        kwargs={},
        output_path="data/logs/profile_report.md"
    )
    
    if not success:
        logger.error("Profiling completed but runtime exceeded limits.")
        sys.exit(1)
    else:
        logger.info("Profiling completed successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()
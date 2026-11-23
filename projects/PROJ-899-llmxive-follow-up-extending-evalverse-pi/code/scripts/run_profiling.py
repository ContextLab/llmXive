import os
import sys
import logging
from pathlib import Path
from src.data.profiles import main as profiling_main
from src.utils import setup_logging

def main():
    """
    Main entry point for the profiling script.
    
    This script runs the profiling batch processing to measure
    CPU time and memory usage for each clip.
    """
    # Setup logging
    logger = setup_logging("run_profiling")
    
    try:
        # Run profiling
        result = profiling_main()
        
        if result == 0:
            logger.info("Profiling completed successfully")
            return 0
        else:
            logger.error("Profiling completed with errors")
            return 1
            
    except Exception as e:
        logger.exception(f"Profiling failed with exception: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
"""
Script to run the profiling execution (T023b).
Profiles CPU time and memory usage for clip processing.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.profiles import main as profiling_main
from src.utils import setup_logging

def main():
    """Main entry point for profiling script."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Running profiling execution (T023b)...")
    
    try:
        exit_code = profiling_main()
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"Profiling execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
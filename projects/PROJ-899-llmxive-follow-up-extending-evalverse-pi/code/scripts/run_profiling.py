"""
Script to run the profiling module for measuring CPU time and memory usage.
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

def main() -> None:
    """Main entry point for the profiling script."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting profiling script")
    
    try:
        profiling_main()
        logger.info("Profiling completed successfully")
    except Exception as e:
        logger.error(f"Profiling failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
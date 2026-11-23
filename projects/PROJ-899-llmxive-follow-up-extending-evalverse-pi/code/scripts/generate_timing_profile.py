import os
import sys
import logging
from pathlib import Path

# Add code root to path
code_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(code_root))

from src.models.evaluate import generate_timing_profile
from src.utils import setup_logging

def main():
    """
    Script entry point for T024: Generate Timing Profile.
    Reads profiling logs and calculates projected time for 10k clips.
    """
    setup_logging(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting T024: Generate Timing Profile")
    
    try:
        generate_timing_profile()
        logger.info("T024 completed successfully")
    except Exception as e:
        logger.error(f"T024 failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
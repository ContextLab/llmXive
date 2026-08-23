import os
import sys
import logging
from pathlib import Path

# Add code to path
code_root = Path(__file__).parent.parent
sys.path.insert(0, str(code_root))

from src.models.evaluate import generate_timing_profile
from src.utils import setup_logging

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Executing T024: Generate Timing Profile")
    
    try:
        output_path = generate_timing_profile()
        logger.info(f"Successfully generated {output_path}")
        return 0
    except Exception as e:
        logger.error(f"Failed to generate timing profile: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
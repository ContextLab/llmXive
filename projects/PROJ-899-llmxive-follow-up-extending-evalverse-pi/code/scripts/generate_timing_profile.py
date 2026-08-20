import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.evaluate import generate_timing_profile, load_scaling_profile
from src.utils import get_logger, ensure_directories

logger = get_logger(__name__)

def main_wrapper() -> int:
    """Wrapper for the timing profile generation script."""
    try:
        logger.info("Executing timing profile generation script (T024)...")
        output_path = generate_timing_profile()
        logger.info(f"Successfully generated timing profile at {output_path}")
        return 0
    except FileNotFoundError as e:
        logger.error(f"Required data file missing: {e}")
        logger.error("Ensure T022 (batch profiling) and T023b (logging) have run successfully.")
        return 1
    except Exception as e:
        logger.error(f"Error during timing profile generation: {e}")
        return 1

def main():
    sys.exit(main_wrapper())

if __name__ == "__main__":
    main()
import os
import sys
import logging
from pathlib import Path

# Add code directory to path
code_root = Path(__file__).resolve().parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.models.evaluate import generate_timing_profile, load_scaling_profile
from src.utils import get_logger, ensure_directories

def main():
    """
    Script wrapper for T024: Generate timing profile.
    """
    logger = get_logger(__name__)
    logger.info("Running timing profile generation (T024)...")
    
    try:
        # Generate the timing profile CSV
        result_df = generate_timing_profile()
        
        logger.info(f"Timing profile generated successfully: {result_df.to_dict('records')}")
        return 0
        
    except Exception as e:
        logger.error(f"Failed to generate timing profile: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
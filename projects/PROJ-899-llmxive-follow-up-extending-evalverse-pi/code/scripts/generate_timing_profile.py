"""
Script to generate timing profile from profiling data.
"""
import os
import sys
import logging
from pathlib import Path
from src.models.evaluate import generate_timing_profile, load_scaling_profile
from src.utils import get_logger
from src.config import get_data_root

logger = get_logger(__name__)

def main_wrapper():
    """Main wrapper for timing profile generation."""
    try:
        # Load profiling data
        profiling_path = os.path.join(get_data_root(), "profiling_logs.json")
        if not os.path.exists(profiling_path):
            logger.error(f"Profiling data not found: {profiling_path}")
            return 1

        import json
        with open(profiling_path, 'r') as f:
            profiling_data = json.load(f)

        # Generate timing profile
        df = generate_timing_profile(profiling_data)

        logger.info(f"Generated timing profile with {len(df)} rows")
        return 0

    except Exception as e:
        logger.error(f"Error generating timing profile: {e}")
        return 1

def main():
    """Main entry point."""
    sys.exit(main_wrapper())

if __name__ == "__main__":
    main()

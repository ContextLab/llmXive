import os
import sys
import logging
from pathlib import Path

# Add code directory to path
code_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(code_root))

from src.data.extract_audio import main
from src.utils import setup_logging

def main_wrapper():
    """Wrapper to run audio extraction with proper logging setup."""
    logger = setup_logging("run_audio_extraction")
    try:
        main()
    except Exception as e:
        logger.error(f"Audio extraction failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main_wrapper()

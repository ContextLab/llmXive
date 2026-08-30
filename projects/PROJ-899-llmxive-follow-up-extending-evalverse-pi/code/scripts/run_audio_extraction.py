import os
import sys
import logging
from pathlib import Path

# Add code directory to path if not already present
code_root = Path(__file__).parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.data.extract_audio import main
from src.utils import setup_logging

def main_wrapper():
    """Wrapper to run the audio extraction script with proper logging."""
    setup_logging(level=logging.INFO)
    try:
        main()
        return 0
    except Exception as e:
        logging.error(f"Audio extraction failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main_wrapper())

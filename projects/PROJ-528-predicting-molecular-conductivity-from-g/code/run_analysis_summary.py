import os
import sys
import logging

from code.logging_config import setup_logging
from code.analysis_summary import main

def main_run():
    """Entry point for running analysis summary."""
    setup_logging()
    try:
        main()
    except Exception as e:
        logging.error(f"Analysis summary failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main_run()

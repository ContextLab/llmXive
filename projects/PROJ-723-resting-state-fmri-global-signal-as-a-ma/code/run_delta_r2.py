import os
import sys
import logging
from pathlib import Path
from config import ensure_directories
from modeling import main

def main_entry():
    ensure_directories()
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    logger.info("Running Delta R2 Analysis (T023)")
    main()

if __name__ == "__main__":
    main_entry()

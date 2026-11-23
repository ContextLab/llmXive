import os
import sys
import logging
from pathlib import Path

from config import get_config
from utils.logging import setup_logging, get_logger
from analysis.sensitivity_analysis import main as sensitivity_main

def main():
    config = get_config()
    setup_logging(log_dir=config.LOGS_DIR)
    logger = get_logger(__name__)
    
    logger.info("Running T025: Sensitivity Analysis")
    sensitivity_main(logger=logger)

if __name__ == "__main__":
    main()
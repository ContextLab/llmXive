import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.evaluate import main as evaluate_main
from src.utils import setup_logging

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Running Baseline Comparisons (T019)")
    evaluate_main()

if __name__ == "__main__":
    main()